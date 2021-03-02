#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 16:21:35 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import pycountry
import mongoengine

from pymongo import database, ReturnDocument
from dotenv import find_dotenv, load_dotenv

SPECIES2CODE = {
    "Sheep": "OA",
    "Goat": "CH"
}

SMARTERDB = "smarter"
DB_ALIAS = "smarterdb"


def global_connection():
    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    # TODO: track connection somewhere
    return mongoengine.connect(
        SMARTERDB,
        username=os.getenv("MONGODB_ROOT_USER"),
        password=os.getenv("MONGODB_ROOT_PASS"),
        authentication_source='admin',
        alias=DB_ALIAS)


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

    # get breed code from database. Nested documents are nested dicts
    breed_code = mongodb.breeds.find_one(
        {"species": species, "breed.name": breed})["breed"]["code"]

    # derive sequence_name from species
    sequence_name = f"sample{species}"

    # get the sequence number and define smarter id
    sequence_id = getNextSequenceValue(sequence_name, mongodb)

    # padding numbers
    sequence_id = str(sequence_id).zfill(4)

    smarter_id = f"{country_code}{species_code}-{breed_code}-{sequence_id}"

    return smarter_id


class SampleSheep():
    def __init__(self, mongoclient=None, **kwargs):
        # track database connection
        self.__client = mongoclient
        self.__collection = "sampleSheep"

        # those are my smarter ids (which are mandatory for validation)
        self._id = None
        self.smarterId = None
        self.originalId = None

        # those are all others field defined by this instance
        self.__attrs = set()

        for key, value in kwargs.items():
            setattr(self, key, value)
            self.__attrs.add(key)

    def save(self):
        # get a database instance
        db = self.__client[SMARTERDB]
        collection = db[self.__collection]

        # initialize a data object
        data = dict()

        for key in self.__attrs:
            data[key] = getattr(self, key)

        smarter_id = getSmarterId(
            self.species, self.country, self.breed, db)

        data['smarterId'] = smarter_id
        collection.insert_one(data)


class Location(mongoengine.EmbeddedDocument):
    ss_id = mongoengine.StringField()
    version = mongoengine.StringField()
    chrom = mongoengine.StringField()
    position = mongoengine.IntField()
    contig = mongoengine.StringField()
    alleles = mongoengine.StringField()
    illumina_forward = mongoengine.StringField()
    ilmnstrand = mongoengine.StringField()
    strand = mongoengine.StringField()
    imported_from = mongoengine.StringField()


class Consequence(mongoengine.EmbeddedDocument):
    pass


class VariantSheep(mongoengine.Document):
    rs_id = mongoengine.StringField()
    illumina_top = mongoengine.StringField()
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
