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

from enum import Enum
from typing import Union

from pymongo import database, ReturnDocument, MongoClient
from dotenv import find_dotenv, load_dotenv

from .utils import get_project_dir

SPECIES2CODE = {
    "Sheep": "OA",
    "Goat": "CH"
}

SMARTERDB = "smarter"
DB_ALIAS = "smarterdb"
CLIENT = None

# Get an instance of a logger
logger = logging.getLogger(__name__)


class SmarterDBException(Exception):
    pass


def global_connection(database_name: str = SMARTERDB) -> MongoClient:
    """
    Establish a connection to the SMARTER database. Reads environment
    parameters using :py:func:`load_dotenv`, returns a MongoClient object.

    Parameters
    ----------
    database_name : str, optional
        The smarter database. The default is 'smarter'.

    Returns
    -------
    CLIENT : MongoClient
        a mongoclient instance.
    """

    global CLIENT

    if not CLIENT:
        # find .env automagically by walking up directories until it's found,
        # then load up the .env entries as environment variables
        load_dotenv(find_dotenv())

        # track connection somewhere
        CLIENT = mongoengine.connect(
            database_name,
            username=os.getenv("MONGODB_SMARTER_USER"),
            password=os.getenv("MONGODB_SMARTER_PASS"),
            host=os.getenv("MONGODB_SMARTER_HOST", default="localhost"),
            port=os.getenv("MONGODB_SMARTER_PORT", default=27017),
            authentication_source='admin',
            alias=DB_ALIAS,
            uuidRepresentation="standard")

    return CLIENT


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


class SmarterInfo(mongoengine.Document):
    """A class to track database status informations"""

    id = mongoengine.StringField(primary_key=True)
    version = mongoengine.StringField(required=True)
    working_assemblies = mongoengine.DictField()
    plink_specie_opt = mongoengine.DictField()
    last_updated = mongoengine.DateTimeField()

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'smarterInfo'
    }

    def __str__(self):
        return f"{self.id}: {self.version} (self.last_updated)"


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


class Country(mongoengine.Document):
    """A helper class to deal with countries object. Each record is created
    after data import, when database status is updated"""

    alpha_2 = mongoengine.StringField(
        required=True, unique=True, min_length=2, max_length=2)
    alpha_3 = mongoengine.StringField(
        required=True, unique=True, min_length=3, max_length=3)
    name = mongoengine.StringField(required=True, unique=True)
    numeric = mongoengine.IntField(required=True, unique=True)
    official_name = mongoengine.StringField()

    species = mongoengine.ListField(mongoengine.StringField())

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'countries'
    }

    def __init__(self, name: str = None, *args, **kwargs):
        # fix species type if necessary
        if "species" in kwargs:
            if type(kwargs["species"]) == str:
                kwargs["species"] = [kwargs["species"]]

        # initialize base object
        super(Country, self).__init__(*args, **kwargs)

        if name:
            country = pycountry.countries.get(name=name)

            self.alpha_2 = country.alpha_2
            self.alpha_3 = country.alpha_3
            self.name = name
            self.numeric = country.numeric

            if hasattr(country, "official_name"):
                self.official_name = country.official_name

    def __str__(self):
        return f"{self.name} ({self.alpha_2})"


class SupportedChip(mongoengine.Document):
    name = mongoengine.StringField(required=True, unique=True)
    species = mongoengine.StringField(required=True)
    manifacturer = mongoengine.StringField()
    n_of_snps = mongoengine.IntField(default=0)

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'supportedChips'
    }

    def __str__(self):
        return f"'{self.name}' ({self.species})"


class BreedAlias(mongoengine.EmbeddedDocument):
    fid = mongoengine.StringField(required=True)
    dataset = mongoengine.ReferenceField(
        'Dataset',
        db_field="dataset_id")
    country = mongoengine.StringField()

    def __str__(self):
        return f"{self.fid}: {self.dataset}"


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
        'indexes': [
            {
                'fields': [
                    "species",
                    "code"
                ],
                'unique': True,
                'collation': {'locale': 'en', 'strength': 1}
            },
            {
                'fields': [
                    "species",
                    "name"
                ],
                'unique': True,
                'collation': {'locale': 'en', 'strength': 1}
            }
        ]
    }

    def __str__(self):
        return f"{self.name} ({self.code}) {self.species}"


def get_or_create_breed(
        species_class: str, name: str, code: str, aliases: list = []) -> [
            Breed, bool]:
    """
    Get a Breed instance or create a new one (or update a breed adding a new
    :py:class:`BreedAlias`)

    Parameters
    ----------
    species_class : str
        The class of the species (should be 'Goat' or 'Sheep')
    name : str
        The breed full name.
    code : str
        The breed code (unique in Sheep and Goats collections).
    aliases : list, optional
        A list of :py:class:`BreedAlias` objects. The default is [].

    Raises
    ------
    SmarterDBException
        Raised if the breed is not Unique.

    Returns
    -------
    breed : Breed
        A :py:class:`Breed` instance.
    modified : bool
        True is breed is created (or alias updated).
    """

    logger.debug(f"Checking: '{species_class}':'{name}':'{code}'")

    # get a breed object relying on parameters
    qs = Breed.objects(species=species_class, name=name, code=code)

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
            species=species_class,
            name=name,
            code=code,
            aliases=aliases,
            n_individuals=0
        )

    else:
        # should never see this relying on collection unique keys
        raise SmarterDBException(
            f"Got {qs.count()} results for '{species_class}':'{name}': "
            f"'{code}'")

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

    # track the original chip_name with dataset
    chip_name = mongoengine.StringField()

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
        species_class: str,
        country: str,
        breed: str) -> str:
    """
    Generate a new SMARTER ID object using the internal counter collections

    Parameters
    ----------
    species_class : str
        The class of the species (should be 'Goat' or 'Sheep').
    country : str
        The country name of the sample.
    breed : str
        The breed name of the sample.

    Raises
    ------
    SmarterDBException
        Raised when passing a wrong species or no one.

    Returns
    -------
    str
        A new smarter_id.
    """

    # this should be the connection I made
    global SMARTERDB, SPECIES2CODE

    # species_class, country and breed shold be defined
    if not species_class or not country or not breed:
        raise SmarterDBException(
            "species, country and breed should be defined when calling "
            "getSmarterId"
        )

    # get species code
    if species_class not in SPECIES2CODE:
        raise SmarterDBException(
            "Species %s not managed by smarter" % (species_class))

    species_code = SPECIES2CODE[species_class]

    # get country code (two letters)
    country = pycountry.countries.get(name=country)
    country_code = country.alpha_2

    # get breed code from database
    database = mongoengine.connection.get_db(alias=DB_ALIAS)
    breed_code = database.breeds.find_one(
        {"species": species_class, "name": breed})["code"]

    # derive sequence_name from species_class
    sequence_name = f"sample{species_class}"

    # get the sequence number and define smarter id
    sequence_id = getNextSequenceValue(
        sequence_name, database)

    # padding numbers
    sequence_id = str(sequence_id).zfill(9)

    smarter_id = f"{country_code}{species_code}-{breed_code}-{sequence_id}"

    return smarter_id


class SEX(bytes, Enum):
    UNKNOWN = (0, "Unknown")
    MALE = (1, "Male")
    FEMALE = (2, "Female")

    def __new__(cls, value, label):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.label = label
        return obj

    def __str__(self):
        return self.label

    @classmethod
    def from_string(cls, value: str):
        """Get proper type relying on input string

        Args:
            value (str): required sex as string

        Returns:
            SEX: A sex instance (MALE, FEMALE, UNKNOWN)
        """

        if type(value) != str:
            raise SmarterDBException("Provided value should be a 'str' type")

        value = value.upper()

        if value in ['M', 'MALE', "1"]:
            return cls.MALE

        elif value in ['F', 'FEMALE', "2"]:
            return cls.FEMALE

        else:
            logger.debug(
                f"Unmanaged sex '{value}': return '{cls.UNKNOWN}'")
            return cls.UNKNOWN


class Phenotype(mongoengine.DynamicEmbeddedDocument):
    """A class to deal with Phenotype. A dynamic document and not a generic
    DictField since that there can be attributes which could be enforced to
    have certain values. All other attributes could be set without any
    assumptions
    """

    purpose = mongoengine.StringField()
    chest_girth = mongoengine.FloatField()
    height = mongoengine.FloatField()
    length = mongoengine.FloatField()

    def __str__(self):
        return f"{self.to_json()}"


class SAMPLETYPE(Enum):
    FOREGROUND = 'foreground'
    BACKGROUND = 'background'


class SampleSpecies(mongoengine.Document):
    original_id = mongoengine.StringField(required=True)
    smarter_id = mongoengine.StringField(required=True, unique=True)

    country = mongoengine.StringField(required=True)

    # generic species type (required to derive other stuff)
    species_class = None

    breed = mongoengine.StringField(required=True)
    breed_code = mongoengine.StringField(min_length=3)

    # this will be a original_id alias (a different sample name in original
    # data file)
    alias = mongoengine.StringField()

    # required to search a sample relying only on original ID
    dataset = mongoengine.ReferenceField(
        Dataset,
        db_field="dataset_id",
        reverse_delete_rule=mongoengine.DENY
    )

    # add type tag
    type_ = mongoengine.EnumField(SAMPLETYPE, db_field="type", required=True)

    # track the original chip_name with sample
    chip_name = mongoengine.StringField()

    # define enum types for sex
    sex = mongoengine.EnumField(SEX)

    # GPS location
    # NOTE: X, Y where X is longitude, Y latitude
    locations = mongoengine.fields.MultiPointField(
        auto_index=True, default=None)

    # additional (not modelled) metadata
    metadata = mongoengine.DictField(default=None)

    # for phenotypes
    phenotype = mongoengine.EmbeddedDocumentField(Phenotype, default=None)

    meta = {
        'abstract': True,
        'indexes': [
            [("locations", "2dsphere")]
        ]
    }

    def save(self, *args, **kwargs):
        """Custom save method. Deal with smarter_id before save"""

        if not self.smarter_id:
            logger.debug(f"Determining smarter id for {self.original_id}")

            # even is species, country and breed are required fields for
            # SampleSpecies document, their value will not be evaluated until
            # super().save() is called. I can't call it before determining
            # a smarter_id
            self.smarter_id = getSmarterId(
                self.species_class,
                self.country,
                self.breed)

        # default save method
        super(SampleSpecies, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.smarter_id} ({self.breed})"


class SampleSheep(SampleSpecies):
    species = mongoengine.StringField(required=True, default="Ovis aries")

    # generic species type (required to derive other stuff)
    species_class = "Sheep"

    # try to model relationship between samples
    father_id = mongoengine.LazyReferenceField(
        'SampleSheep',
        passthrough=True,
        reverse_delete_rule=mongoengine.NULLIFY
    )

    mother_id = mongoengine.LazyReferenceField(
        'SampleSheep',
        passthrough=True,
        reverse_delete_rule=mongoengine.NULLIFY
    )

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'sampleSheep'
    }


class SampleGoat(SampleSpecies):
    species = mongoengine.StringField(required=True, default="Capra hircus")

    # generic species type (required to derive other stuff)
    species_class = "Goat"

    # try to model relationship between samples
    father_id = mongoengine.LazyReferenceField(
        'SampleGoat',
        passthrough=True,
        reverse_delete_rule=mongoengine.NULLIFY
    )

    mother_id = mongoengine.LazyReferenceField(
        'SampleGoat',
        passthrough=True,
        reverse_delete_rule=mongoengine.NULLIFY
    )

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'sampleGoat'
    }


def get_or_create_sample(
        SampleSpecies: Union[SampleGoat, SampleSheep],
        original_id: str,
        dataset: Dataset,
        type_: str,
        breed: Breed,
        country: str,
        species: str = None,
        chip_name: str = None,
        sex: SEX = None,
        alias: str = None) -> list[Union[SampleGoat, SampleSheep], bool]:
    """
    Get or create a sample providing attributes (search for original_id in
    provided dataset

    Parameters
    ----------
    SampleSpecies : Union[SampleGoat, SampleSheep]
        the class required for insert/update.
    original_id : str
        the original_id in the dataset.
    dataset : Dataset
        the dataset instance used to register sample.
    type_ : str
        sample type. "background" or "foreground" are the only values accepted
    breed : Breed
        a :py:class:`Breed` instance.
    country : str
        the country where the sample comes from.
    species : str, optional
        The sample species. If None, the default `species_class` attribute
        will be used
    chip_name : str, optional
        the chip name. The default is None.
    sex : SEX, optional
        A :py:class:`SEX` instance. The default is None.
    alias : str, optional
         an original_id alias. Could be the name used in the genotype file,
         which could be different from the original_id. The default is None.

    Raises
    ------
    SmarterDBException
        Raised multiple samples are returned (should never happen).

    Returns
    -------
    Union[SampleGoat, SampleSheep]
        a SampleSpecies instance.
    created : bool
        True is sample is created.
    """

    created = False

    # search for sample in database
    qs = SampleSpecies.objects(
        original_id=original_id, breed_code=breed.code, dataset=dataset)

    if qs.count() == 1:
        logger.debug(f"Sample '{original_id}' found in database")
        sample = qs.get()

    elif qs.count() == 0:
        # insert sample into database
        logger.info(f"Registering sample '{original_id}' in database")
        sample = SampleSpecies(
            original_id=original_id,
            country=country,
            species=species,
            breed=breed.name,
            breed_code=breed.code,
            dataset=dataset,
            type_=type_,
            chip_name=chip_name,
            sex=sex,
            alias=str(alias)
        )
        sample.save()

        # incrementing breed n_individuals counter
        breed.n_individuals += 1
        breed.save()

        created = True

    else:
        raise SmarterDBException(
            f"Got {qs.count()} results for '{original_id}'")

    return sample, created


def get_sample_type(dataset: Dataset):
    """
    test if foreground or background dataset

    Args:
        dataset (Dataset): the dataset instance used to register sample

    Returns:
        str: sample type ("background" or "foreground")
    """

    type_ = None

    for sampletype in SAMPLETYPE:
        if sampletype.value in dataset.type_:
            logger.debug(
                f"Found {sampletype.value} in {dataset.type_}")
            type_ = sampletype.value
            break

    return type_


class Consequence(mongoengine.EmbeddedDocument):
    pass


class Location(mongoengine.EmbeddedDocument):
    ss_id = mongoengine.StringField()
    version = mongoengine.StringField(required=True)
    chrom = mongoengine.StringField(required=True)
    position = mongoengine.IntField(required=True)
    alleles = mongoengine.StringField()
    illumina = mongoengine.StringField(required=True)
    illumina_forward = mongoengine.StringField()
    illumina_strand = mongoengine.StringField()
    affymetrix_ab = mongoengine.StringField()
    strand = mongoengine.StringField()
    imported_from = mongoengine.StringField(required=True)

    # this could be the manifactured date or the last updated
    date = mongoengine.DateTimeField()

    consequences = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Consequence), default=None)

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

        if not getattr(self, coding):
            raise SmarterDBException(
                f"There's no information for '{coding}' in '{self}'")

        # get illumina data as an array
        data = getattr(self, coding).split("/")

        for allele in genotype:
            # mind to missing values. If missing can't be equal to illumina_top
            if allele in missing:
                continue

            if allele not in data:
                return False

        return True

    def is_top(self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with illumina TOP coding

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (str): missing allele string (def "0")

        Returns:
            bool: True if in top coordinates
        """

        return self.__check_coding(genotype, "illumina_top", missing)

    def is_forward(self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with illumina FORWARD coding

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (str): missing allele string (def "0")

        Returns:
            bool: True if in top coordinates
        """

        return self.__check_coding(genotype, "illumina_forward", missing)

    def is_ab(self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with illumina AB coding

        Args:
            genotype (list): a list of two alleles (ex ['A','B'])
            missing (str): missing allele string (def "-")

        Returns:
            bool: True if in top coordinates
        """

        for allele in genotype:
            # mind to missing valies
            if allele not in ["A", "B"] + missing:
                return False

        return True

    def is_affymetrix(
            self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with affymetrix coding

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (str): missing allele string (def "0")

        Returns:
            bool: True if in top coordinates
        """

        return self.__check_coding(genotype, "affymetrix_ab", missing)

    def forward2top(self, genotype: list, missing: list = ["0", "-"]) -> list:
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
            if allele in missing:
                result.append("0")

            elif allele not in forward:
                raise SmarterDBException(
                    f"{genotype} is not in forward coding")

            else:
                result.append(top[forward.index(allele)])

        return result

    def ab2top(self, genotype: list, missing: list = ["0", "-"]) -> list:
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
            if allele in missing:
                result.append("0")

            elif allele not in ["A", "B"]:
                raise SmarterDBException(
                    f"{genotype} is not in ab coding")

            else:
                result.append(top[allele])

        return result

    def affy2top(self, genotype: list, missing: list = ["0", "-"]) -> list:
        """Convert an affymetrix SNP in a illumina top snp

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (str): missing allele string (def "0")

        Returns:
            list: The genotype in top format
        """

        # get illumina data as an array
        affymetrix = self.affymetrix_ab.split("/")
        top = self.illumina_top.split("/")

        result = []

        for allele in genotype:
            # mind to missing values
            if allele in missing:
                result.append("0")

            elif allele not in affymetrix:
                raise SmarterDBException(
                    f"{genotype} is not in affymetrix coding")

            else:
                result.append(top[affymetrix.index(allele)])

        return result


class Probeset(mongoengine.EmbeddedDocument):
    chip_name = mongoengine.StringField(required=True)

    # more probe could be assigned to the same SNP
    probeset_id = mongoengine.ListField(mongoengine.StringField())

    def __str__(self):
        return (
            f"{self.chip_name}: {self.probeset_id}"
        )


class VariantSpecies(mongoengine.Document):
    rs_id = mongoengine.ListField(mongoengine.StringField(), default=None)
    chip_name = mongoengine.ListField(mongoengine.StringField())

    name = mongoengine.StringField(unique=True)

    # sequence should model both illumina or affymetrix sequences
    sequence = mongoengine.DictField()

    # illumina top variant at variant level
    illumina_top = mongoengine.StringField(required=True)

    locations = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Location))

    # HINT: should sender be a Location attribute?
    sender = mongoengine.StringField()

    # Affymetryx specific fields
    probesets = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Probeset), default=None)
    affy_snp_id = mongoengine.StringField()
    cust_id = mongoengine.StringField()

    # abstract class with custom indexes
    # TODO: need a index for position (chrom, position, version)
    meta = {
        'abstract': True,
        'indexes': [
            {
                'fields': [
                    "locations.chrom",
                    "locations.position"
                ],
            },
            {
                'fields': ["affy_snp_id"],
                'partialFilterExpression': {
                    "affy_snp_id": {
                        "$exists": True
                    }
                }
            },
            "probesets.probeset_id",
            'rs_id',
        ]
    }

    def __str__(self):
        if not self.name and self.affy_snp_id:
            return (
                f"affy_snp_id='{self.affy_snp_id}', rs_id='{self.rs_id}', "
                f"illumina_top='{self.illumina_top}'")

        return (
            f"name='{self.name}', rs_id='{self.rs_id}', "
            f"illumina_top='{self.illumina_top}'")

    def save(self, *args, **kwargs):
        """Custom save method. Deal with variant name before save"""

        if not self.name and self.affy_snp_id:
            logger.debug(f"Set variant name to {self.affy_snp_id}")
            self.name = self.affy_snp_id

        # default save method
        super(VariantSpecies, self).save(*args, **kwargs)

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


class VariantSheep(VariantSpecies):
    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'variantSheep'
    }


class VariantGoat(VariantSpecies):
    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'variantGoat'
    }
