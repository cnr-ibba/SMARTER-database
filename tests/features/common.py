#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 17:44:00 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

from mongoengine import connect, disconnect, connection

from src.features.smarterdb import (
    DB_ALIAS, Breed, BreedAlias, Counter, Dataset, SampleSheep)


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
            dataset=dataset
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
