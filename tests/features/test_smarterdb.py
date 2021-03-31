#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 17:32:28 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import unittest
import pathlib

from mongoengine import connect, disconnect

from src.features.smarterdb import (
    VariantSheep, Location, DB_ALIAS, SampleSheep, Breed, Counter,
    SmarterDBException)


# set data dir (like os.dirname(__file__)) + "fixtures"
DATA_DIR = pathlib.Path(__file__).parent / "fixtures"


class MongoMock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        connect(
            'mongoenginetest',
            host='mongomock://localhost',
            alias=DB_ALIAS)

    @classmethod
    def tearDownClass(cls):
        disconnect()


class VariantSheepTestCase(MongoMock):
    @classmethod
    def setUpClass(cls):
        with open(DATA_DIR / "variant.json") as handle:
            cls.data = json.load(handle)

        super().setUpClass()

    def setUp(self):
        self.variant = VariantSheep.from_json(json.dumps(self.data))

    def test__str(self):
        self.assertEqual(
            str(self.variant),
            "name='250506CS3900065000002_1238.1', rs_id='rs55630613'"
        )

    def test_location(self):
        "get a specific location from VariantSheep"

        reference = self.data["locations"][1]
        reference = Location.from_json(json.dumps(reference))

        test = self.variant.get_location(
            version="Oar_v3.1",
            imported_from='SNPchiMp v.3'
        )

        self.assertEqual(reference, test)

    def test_no_location(self):
        "Search for a location not present in database raise exception"

        self.assertRaisesRegex(
            SmarterDBException,
            "Couldn't determine a unique location for",
            self.variant.get_location,
            version="Oar_v4.0",
            imported_from='SNPchiMp v.3'
        )


class SampleSheepTestCase(MongoMock):
    @classmethod
    def setUpClass(cls):
        # need to define a breed in order to get a smarter id
        cls.breed = Breed(
            species="Sheep",
            name="Texel",
            code="TEX"
        )
        cls.breed.save()

        # need also a counter object
        cls.counter = Counter(
            pk="sampleSheep",
            sequence_value=0
        )
        cls.counter.save()

        super().setUpClass()

    def setUp(self):
        self.smarter_id = None
        self.original_id = "TEST"

        self.sample = SampleSheep(
            original_id=self.original_id,
            smarter_id=self.smarter_id
        )

    def test__str(self):
        self.assertEqual(
            str(self.sample),
            f"{self.smarter_id} ({self.original_id})"
        )

    def test_save(self):
        # need country, breed and species in order to get a smarter_id
        self.sample.country = "Italy"
        self.sample.breed = "Texel"
        self.sample.species = "Sheep"

        # save sample in db
        self.sample.save()

        # this will be the reference smarter_id
        reference = "ITOA-TEX-0001"

        self.assertEqual(self.sample.smarter_id, reference)


if __name__ == '__main__':
    unittest.main()
