#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 17:44:00 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import pathlib
import logging

from dateutil.parser import parse as parse_date

import mongomock
from mongoengine import connect, disconnect, connection

import src.features.smarterdb
from src.features.smarterdb import (
    DB_ALIAS, Breed, BreedAlias, Counter, Dataset, SampleSheep, VariantSheep,
    VariantGoat, SupportedChip)

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"

# Get an instance of a logger
logger = logging.getLogger(__name__)


class MongoMockMixin():
    @classmethod
    def setUpClass(cls):
        src.features.smarterdb.CLIENT = connect(
            'mongoenginetest',
            host='mongodb://localhost',
            mongo_client_class=mongomock.MongoClient,
            alias=DB_ALIAS)

        _ = connection.get_db(alias=DB_ALIAS)

    @classmethod
    def tearDownClass(cls):
        disconnect()


class SmarterIDMixin():
    """Common set up for classes which require a smarter id to work properly"""
    @classmethod
    def setUpClass(cls):
        # initialize the mongomock instance
        super().setUpClass()

        # need a dataset for certain tests
        cls.dataset = Dataset(
            file="test.zip",
            country="Italy",
            species="Sheep",
            contents=[
                "plinktest.map",
                "plinktest.ped",
                "plinktest.fam",
                "plinktest.bim",
                "plinktest.bed",
                "snplist.txt",
                "snplist_3cols.txt",
                "finalreport.txt",
                "affytest.map",
                "affytest.ped",
                "affyreport.txt",
                "affyreport_nocols.txt"
            ],
            type_=["background", "genotypes"],
            doi="https://example.com"
        )
        cls.dataset.save()

        # need to define a breed in order to get a smarter id
        cls.alias = BreedAlias(
            fid="TEX_IT",
            dataset=cls.dataset,
            country="Italy"
        )

        cls.breed = Breed(
            species="Sheep",
            name="Texel",
            code="TEX",
            n_individuals=0,
            aliases=[cls.alias]
        )
        cls.breed.save()

        # create additional breed
        alias = BreedAlias(
            fid="MER_IT",
            dataset=cls.dataset,
            country="Italy"
        )

        cls.breed2 = Breed(
            species="Sheep",
            name="Merino",
            code="MER",
            n_individuals=0,
            aliases=[alias]
        )
        cls.breed2.save()

        # need also a counter object for sheep and goat
        counter = Counter(
            pk="sampleSheep",
            sequence_value=0
        )
        counter.save()

        counter = Counter(
            pk="sampleGoat",
            sequence_value=0
        )
        counter.save()

    def tearDown(self):
        """Reset all to initial state"""

        # drop created samples
        SampleSheep.objects.delete()

        # reset counters
        Counter.objects.update(sequence_value=0)

        # reset breed counters
        Breed.objects.update(n_individuals=0)

        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        # delete created objects
        Breed.objects().delete()
        Counter.objects().delete()
        Dataset.objects().delete()

        super().tearDownClass()


def sanitize_dict(record: dict):
    """Remove unsupported mongoengine keys from a dictionary"""

    if '_id' in record:
        logger.debug(f"remove key '_id': {record['_id']}")
        del(record['_id'])

    for key, value in record.items():
        if isinstance(value, dict):
            record[key] = sanitize_dict(value)

            if '$date' in value:
                logger.debug(f"fix '{key}': {value['$date']}")
                record[key] = parse_date(value['$date'])

        elif isinstance(value, list):
            record[key] = sanitize_list(value)

    return record


def sanitize_list(record: list):
    """Remove unsupported mongoengine keys from a list"""

    for i, item in enumerate(record):
        if isinstance(item, dict):
            record[i] = sanitize_dict(item)

        if isinstance(item, list):
            record[i] = sanitize_list(item)

    return record


class VariantSpecieMixin():
    variant_fixture = None
    variant_species = None

    @classmethod
    def setUpClass(cls):
        # initialize the mongomock instance
        super().setUpClass()

        # load database variants into mock database
        with open(FIXTURES_DIR / cls.variant_fixture) as handle:
            cls.data = json.load(handle)

        # I can't track data with from_json like mongoengine does. I need
        # to instantiate objects from dict (without unsupported keys)
        for item in cls.data:
            # remove unsupported keys
            item = sanitize_dict(item)

            variant = cls.variant_species(**item)
            variant.save()

    @classmethod
    def tearDownClass(cls):
        cls.variant_species.objects.delete()

        super().tearDownClass()


class VariantSheepMixin(VariantSpecieMixin):
    # This will be the default fixture loaded by this class
    variant_fixture = "sheep_variants.json"
    variant_species = VariantSheep


class VariantGoatMixin(VariantSpecieMixin):
    # This will be the default fixture loaded by this class
    variant_fixture = "goat_variants.json"
    variant_species = VariantGoat


class SupportedChipMixin():
    chip_name = "IlluminaOvineSNP50"
    manufacturer = "illumina"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.chip = SupportedChip(
            name=cls.chip_name,
            manufacturer=cls.manufacturer,
            species="Sheep")
        cls.chip.save()

    @classmethod
    def tearDownClass(cls):
        SupportedChip.objects.delete()

        super().tearDownClass()
