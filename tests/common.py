#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 17:44:00 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import pathlib

from mongoengine import connect, disconnect, connection

from src.features.smarterdb import (
    DB_ALIAS, Breed, BreedAlias, Counter, Dataset, SampleSheep, VariantSheep,
    SupportedChip)

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


class MongoMockMixin():
    @classmethod
    def setUpClass(cls):
        connect(
            'mongoenginetest',
            host='mongomock://localhost',
            alias=DB_ALIAS)

        cls.connection = connection.get_db(alias=DB_ALIAS)

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
        dataset = Dataset(
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
                "finalreport.txt"
            ]
        )
        dataset.save()

        # need to define a breed in order to get a smarter id
        alias = BreedAlias(
            fid="TEX_IT",
            dataset=dataset,
            country="Italy"
        )

        breed = Breed(
            species="Sheep",
            name="Texel",
            code="TEX",
            n_individuals=0,
            aliases=[alias]
        )
        breed.save()

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


class VariantsMixin():
    @classmethod
    def setUpClass(cls):
        # initialize the mongomock instance
        super().setUpClass()

        # load database variants into mock database
        with open(FIXTURES_DIR / "variants.json") as handle:
            cls.data = json.load(handle)

        # I can't track data with from_json like mongoengine does. I need
        # to instantiate objects from dict (without unsupported keys)
        for item in cls.data:
            del(item['_id'])
            variant = VariantSheep(**item)
            variant.save()

    @classmethod
    def tearDownClass(cls):
        VariantSheep.objects.delete()

        super().tearDownClass()


class SupportedChipMixin():
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.chip_name = "IlluminaOvineSNP50"
        cls.chip = SupportedChip(name=cls.chip_name, species="Sheep")
        cls.chip.save()

    @classmethod
    def tearDownClass(cls):
        SupportedChip.objects.delete()

        super().tearDownClass()
