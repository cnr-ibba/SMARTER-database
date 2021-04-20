#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 16:21:35 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import logging
import pathlib
import pycountry
import mongoengine

from pymongo import database, ReturnDocument
from dotenv import find_dotenv, load_dotenv

from .utils import get_project_dir

SPECIES2CODE = {
    "Sheep": "OA",
    "Goat": "CH"
}

SMARTERDB = "smarter"
DB_ALIAS = "smarterdb"

# Get an instance of a logger
logger = logging.getLogger(__name__)


class SmarterDBException(Exception):
    pass


def global_connection(database_name: str = SMARTERDB):
    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    # TODO: track connection somewhere
    return mongoengine.connect(
        database_name,
        username=os.getenv("MONGODB_SMARTER_USER"),
        password=os.getenv("MONGODB_SMARTER_PASS"),
        authentication_source='admin',
        alias=DB_ALIAS)


def complement(genotype: str):
    bases = {
        "A": "T",
        "T": "A",
        "C": "G",
        "G": "C",
        "/": "/"
    }

    result = ""

    for base in genotype:
        result += bases[base]

    return result


class Counter(mongoengine.Document):
    """A class to deal with counter collection (created when initializing
    smarter database)
    """

    id = mongoengine.StringField(primary_key=True)
    sequence_value = mongoengine.IntField(required=True, default=0)

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'counters'
    }

    def __str__(self):
        return f"{self.id}: {self.sequence_value}"


class BreedAlias(mongoengine.EmbeddedDocument):
        fid = mongoengine.StringField(required=True)
        dataset = mongoengine.ReferenceField('Dataset', db_field="dataset_id")


class Breed(mongoengine.Document):
    species = mongoengine.StringField(required=True)
    name = mongoengine.StringField(required=True)
    code = mongoengine.StringField(required=True)
    aliases = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(BreedAlias))
    n_individuals = mongoengine.IntField()

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'breeds',
        'indexes': [{
            'fields': [
                "species",
                "code"
            ],
            'unique': True,
            'collation': {'locale': 'en', 'strength': 1}
        }]
    }

    def __str__(self):
        return f"{self.name} ({self.code}) {self.species}"


def get_or_create_breed(
        species: str, name: str, code: str, aliases: list = []):

    logger.debug(f"Checking: '{species}':'{name}':'{code}'")

    # get a breed object relying on parameters
    qs = Breed.objects(species=species, name=name, code=code)

    modified = False

    if qs.count() == 1:
        breed = qs.get()
        logger.debug(f"Got {breed}")
        for alias in aliases:
            if alias not in breed.aliases:
                # track for update
                modified = True

                logger.info(f"Adding '{alias}' to '{breed}' aliases")
                breed.aliases.append(alias)

    elif qs.count() == 0:
        logger.debug("Create a new breed object")
        modified = True

        breed = Breed(
            species=species,
            name=name,
            code=code,
            aliases=aliases,
            n_individuals=0
        )

    else:
        # should never see this relying on collection unique keys
        raise SmarterDBException(
            f"Got {qs.count()} results for '{species}':'{name}':'{code}'")

    if modified:
        logger.debug(f"Save '{breed}' to database")
        breed.save()

    return breed, modified


class Dataset(mongoengine.Document):
    """Describe a dataset instace with fields owned by data types"""

    file = mongoengine.StringField(required=True, unique=True)
    uploader = mongoengine.StringField()
    size_ = mongoengine.StringField(db_field="size")
    partner = mongoengine.StringField()

    # HINT: should country, species and breeds be a list of items?
    country = mongoengine.StringField()
    species = mongoengine.StringField()
    breed = mongoengine.StringField()

    n_of_individuals = mongoengine.IntField()
    n_of_records = mongoengine.IntField()
    trait = mongoengine.StringField()
    gene_array = mongoengine.StringField()

    # add type tag
    type_ = mongoengine.ListField(mongoengine.StringField(), db_field="type")

    # file contents
    contents = mongoengine.ListField(mongoengine.StringField())

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'dataset'
    }

    def __str__(self):
        return f"file={self.file}, uploader={self.uploader}"

    @property
    def working_dir(self) -> pathlib.PosixPath:
        """returns the locations of dataset working directory. Could exists
        or not

        Returns:
            pathlib.PosixPath: a subdirectory in /data/interim/
        """

        if not self.id:
            raise SmarterDBException(
                "Can't define working dir. Object need to be stored in "
                "database")

        return get_project_dir() / f"data/interim/{self.id}"

    @property
    def result_dir(self) -> pathlib.PosixPath:
        """returns the locations of dataset processed directory. Could exists
        or not

        Returns:
            pathlib.PosixPath: a subdirectory in /data/processed/
        """

        if not self.id:
            raise SmarterDBException(
                "Can't define result dir. Object need to be stored in "
                "database")

        return get_project_dir() / f"data/processed/{self.id}"


def getNextSequenceValue(
        sequence_name: str, mongodb: database.Database):
    # this method is something similar to findAndModify,
    # update a document and after get the UPDATED document
    # https://docs.mongodb.com/manual/reference/method/db.collection.findAndModify/index.html#db.collection.findAndModify
    sequenceDocument = mongodb.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        return_document=ReturnDocument.AFTER
    )

    return sequenceDocument['sequence_value']


def getSmarterId(
        species: str, country: str, breed: str, mongodb: database.Database):

    # species, country and breed shold be defined in order to call this func
    if not species or not country or not breed:
        raise SmarterDBException(
            "species, country and breed should be defined when calling "
            "getSmarterId"
        )

    # get species code
    if species not in SPECIES2CODE:
        raise SmarterDBException(
            "Species %s not managed by smarter" % (species))

    species_code = SPECIES2CODE[species]

    # get country code (two letters)
    country = pycountry.countries.get(name=country)
    country_code = country.alpha_2

    # get breed code from database
    breed_code = mongodb.breeds.find_one(
        {"species": species, "name": breed})["code"]

    # derive sequence_name from species
    sequence_name = f"sample{species}"

    # get the sequence number and define smarter id
    sequence_id = getNextSequenceValue(sequence_name, mongodb)

    # padding numbers
    sequence_id = str(sequence_id).zfill(9)

    smarter_id = f"{country_code}{species_code}-{breed_code}-{sequence_id}"

    return smarter_id


class SampleSheep(mongoengine.Document):
    original_id = mongoengine.StringField(required=True)
    smarter_id = mongoengine.StringField(required=True, unique=True)

    country = mongoengine.StringField(required=True)
    species = mongoengine.StringField(required=True)
    breed = mongoengine.StringField(required=True)
    breed_code = mongoengine.StringField(max_length=3, min_length=3)

    # required to search a sample relying only on original ID
    dataset = mongoengine.ReferenceField(Dataset, db_field="dataset_id")

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'sampleSheep'
    }

    def save(self, *args, **kwargs):
        """Custom save method. Deal with smarter_id before save"""

        if not self.smarter_id:
            logger.debug(f"Determining smarter id for {self.original_id}")

            # get the pymongo connection object
            conn = mongoengine.connection.get_db(alias=DB_ALIAS)

            # even is species, country and breed are required fields for
            # SampleSheep document, their value will not be evaluated until
            # super().save() is called. I can't call it before determining
            # a smarter_id
            self.smarter_id = getSmarterId(
                self.species,
                self.country,
                self.breed,
                conn)

        # default save method
        super(SampleSheep, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.smarter_id} ({self.original_id})"


class Consequence(mongoengine.EmbeddedDocument):
    pass


class Location(mongoengine.EmbeddedDocument):
    ss_id = mongoengine.StringField()
    version = mongoengine.StringField()
    chrom = mongoengine.StringField()
    position = mongoengine.IntField()
    contig = mongoengine.StringField()
    alleles = mongoengine.StringField()
    illumina = mongoengine.StringField()
    illumina_forward = mongoengine.StringField()
    illumina_strand = mongoengine.StringField()
    strand = mongoengine.StringField()
    imported_from = mongoengine.StringField()

    consequences = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Consequence))

    def __init__(self, *args, **kwargs):
        illumina_top = None

        # remove illumina top from arguments
        if 'illumina_top' in kwargs:
            illumina_top = kwargs.pop('illumina_top')

        # initialize base object
        super(Location, self).__init__(*args, **kwargs)

        # fix illumina top if necessary
        if illumina_top:
            self.illumina_top = illumina_top

    @property
    def illumina_top(self):
        """Return genotype in illumina top format"""

        if self.illumina_strand in ['BOT', 'bottom']:
            return complement(self.illumina)

        elif (not self.illumina_strand or
              self.illumina_strand in ['TOP', 'top']):
            return self.illumina

        else:
            raise SmarterDBException(
                f"{self.illumina_strand} not managed")

    @illumina_top.setter
    def illumina_top(self, genotype: str):
        if (not self.illumina_strand or
                self.illumina_strand in ['TOP', 'top']):
            self.illumina = genotype

        elif self.illumina_strand in ['BOT', 'bottom']:
            self.illumina = complement(genotype)

        else:
            raise SmarterDBException(
                f"{self.illumina_strand} not managed")

    def __str__(self):
        return (
            f"({self.imported_from}:{self.version}) "
            f"{self.chrom}:{self.position} [{self.illumina_top}]"
        )

    def __eq__(self, other):
        if super().__eq__(other):
            return True

        else:
            # check by positions
            for attribute in ["chrom", "position"]:
                if getattr(self, attribute) != getattr(other, attribute):
                    return False

            # check genotype equality
            if self.illumina_top != other.illumina_top:
                return False

            return True

    def __check_coding(self, genotype: list, coding: str, missing: str):
        """Internal method to check genotype coding"""

        # get illumina data as an array
        data = getattr(self, coding).split("/")

        for allele in genotype:
            # mind to missing values. If missing can't be equal to illumina_top
            if allele == missing:
                continue

            if allele not in data:
                return False

        return True

    def is_top(self, genotype: list, missing: str = "0") -> bool:
        """Return True if genotype is compatible with illumina TOP coding

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (str): missing allele string (def "0")

        Returns:
            bool: True if in top coordinates
        """

        return self.__check_coding(genotype, "illumina_top", missing)

    def is_forward(self, genotype: list, missing: str = "0") -> bool:
        """Return True if genotype is compatible with illumina FORWARD coding

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (str): missing allele string (def "0")

        Returns:
            bool: True if in top coordinates
        """

        return self.__check_coding(genotype, "illumina_forward", missing)

    def is_ab(self, genotype: list, missing: str = "-") -> bool:
        """Return True if genotype is compatible with illumina AB coding

        Args:
            genotype (list): a list of two alleles (ex ['A','B'])
            missing (str): missing allele string (def "0")

        Returns:
            bool: True if in top coordinates
        """

        for allele in genotype:
            # mind to missing valies
            if allele not in ["A", "B", missing]:
                return False

        return True

    def forward2top(self, genotype: list, missing: str = "0") -> list:
        """Convert an illumina forward SNP in a illumina top snp

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (str): missing allele string (def "0")

        Returns:
            list: The genotype in top format
        """

        # get illumina data as an array
        forward = self.illumina_forward.split("/")
        top = self.illumina_top.split("/")

        result = []

        for allele in genotype:
            # mind to missing values
            if allele == missing:
                result.append(allele)

            elif allele not in forward:
                raise SmarterDBException(
                    "{genotype} is not in forward coding")

            else:
                result.append(top[forward.index(allele)])

        return result

    def ab2top(self, genotype: list, missing: str = "-") -> list:
        """Convert an illumina ab SNP in a illumina top snp

        Args:
            genotype (list): a list of two alleles (ex ['A','B'])
            missing (str): missing allele string (def "-")

        Returns:
            list: The genotype in top format
        """

        # get illumina data as a dict
        top = self.illumina_top.split("/")
        top = {"A": top[0], "B": top[1]}

        result = []

        for allele in genotype:
            # mind to missing values
            if allele == missing:
                result.append("0")

            elif allele not in ["A", "B"]:
                raise SmarterDBException(
                    "{genotype} is not in ab coding")

            else:
                result.append(top[allele])

        return result


class VariantSheep(mongoengine.Document):
    rs_id = mongoengine.StringField()
    chip_name = mongoengine.ListField(mongoengine.StringField())
    name = mongoengine.StringField(unique=True)
    sequence = mongoengine.StringField()
    locations = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Location))
    sender = mongoengine.StringField()

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'variantSheep'
    }

    def __str__(self):
        return (f"name='{self.name}', rs_id='{self.rs_id}'")

    def get_location_index(self, version: str, imported_from='SNPchiMp v.3'):
        """Returns location index for assembly version and imported source

        Args:
            version (str): assembly version (ex: 'Oar_v3.1')
            imported_from (str): coordinates source (ex: 'SNPchiMp v.3')

        Returns:
            int: the index of the location requested
        """

        for index, location in enumerate(self.locations):
            if (location.version == version and
                    location.imported_from == imported_from):
                return index

        raise SmarterDBException(
                f"Location '{version}' '{imported_from}' is not in locations"
        )

    def get_location(self, version: str, imported_from='SNPchiMp v.3'):
        """Returns location for assembly version and imported source

        Args:
            version (str): assembly version (ex: 'Oar_v3.1')
            imported_from (str): coordinates source (ex: 'SNPchiMp v.3')

        Returns:
            Location: the genomic coordinates
        """

        def custom_filter(location: Location):
            if (location.version == version and
                    location.imported_from == imported_from):
                return True

            return False

        locations = list(filter(custom_filter, self.locations))

        if len(locations) != 1:
            raise SmarterDBException(
                "Couldn't determine a unique location for "
                f"'{self.name}' '{version}' '{imported_from}'")

        return locations[0]
