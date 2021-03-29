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


class Breed(mongoengine.Document):
    species = mongoengine.StringField(required=True)
    name = mongoengine.StringField(required=True)
    code = mongoengine.StringField(required=True)
    aliases = mongoengine.ListField(mongoengine.StringField())
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
            raise Exception(
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
            raise Exception(
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
    # get species code
    if species not in SPECIES2CODE:
        raise Exception("Species %s not managed by smarter" % (species))

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
    sequence_id = str(sequence_id).zfill(4)

    smarter_id = f"{country_code}{species_code}-{breed_code}-{sequence_id}"

    return smarter_id


class SampleSheep(mongoengine.Document):
    original_id = mongoengine.StringField(required=True)
    smarter_id = mongoengine.StringField(required=True, unique=True)

    country = mongoengine.StringField()
    species = mongoengine.StringField()
    breed = mongoengine.StringField()
    breed_code = mongoengine.StringField(max_length=3, min_length=3)

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

            self.smarter_id = getSmarterId(
                self.species,
                self.country,
                self.breed,
                conn)

        # default save method
        super(SampleSheep, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.smarter_id} ({self.original_id})"


class Location(mongoengine.EmbeddedDocument):
    ss_id = mongoengine.StringField()
    version = mongoengine.StringField()
    chrom = mongoengine.StringField()
    position = mongoengine.IntField()
    contig = mongoengine.StringField()
    alleles = mongoengine.StringField()
    illumina = mongoengine.StringField()
    illumina_top = mongoengine.StringField()
    illumina_forward = mongoengine.StringField()
    illumina_strand = mongoengine.StringField()
    strand = mongoengine.StringField()
    imported_from = mongoengine.StringField()

    def __str__(self):
        return (
            f"({self.imported_from}:{self.version}) "
            f"{self.chrom}:{self.position}"
        )


# HINT: should be relative to location?
class Consequence(mongoengine.EmbeddedDocument):
    pass


class VariantSheep(mongoengine.Document):
    rs_id = mongoengine.StringField()
    chip_name = mongoengine.ListField(mongoengine.StringField())
    name = mongoengine.StringField(unique=True)
    consequences = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Consequence))
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
            raise Exception(
                "Couldn't determine a unique location for "
                f"{self.name} '{version}' '{imported_from}'")

        return locations[0]
