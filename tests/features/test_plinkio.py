#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 17:42:03 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import unittest
import pathlib
import tempfile

from src.features.smarterdb import VariantSheep, Location
from src.features.plinkio import TextPlinkIO, MapRecord

from .common import MongoMockMixin

# set data dir (like os.dirname(__file__)) + "fixtures"
FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"
DATA_DIR = pathlib.Path(__file__).parent / "data"


class SmarterMixin(MongoMockMixin):
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


class TextPlinkIOTestCase(SmarterMixin, unittest.TestCase):
    def setUp(self):
        self.plinkio = TextPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Sheep")

    def test_read_mapfile(self):
        self.plinkio.read_mapfile()
        self.assertIsInstance(self.plinkio.mapdata, list)
        self.assertEqual(len(self.plinkio.mapdata), 4)
        for record in self.plinkio.mapdata:
            self.assertIsInstance(record, MapRecord)

    def test_fetch_coordinates(self):
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(version="Oar_v3.1")

        self.assertIsInstance(self.plinkio.locations, list)
        self.assertEqual(len(self.plinkio.locations), 4)

        self.assertIsInstance(self.plinkio.filtered, set)
        self.assertEqual(len(self.plinkio.filtered), 1)

        # assert filtered items
        self.assertIn(3, self.plinkio.filtered)

        for idx, record in enumerate(self.plinkio.locations):
            if idx in self.plinkio.filtered:
                self.assertIsNone(record)
            else:
                self.assertIsInstance(record, Location)

    def test_update_mapfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.map"
            self.plinkio.read_mapfile()
            self.plinkio.fetch_coordinates(version="Oar_v3.1")
            self.plinkio.update_mapfile(str(outfile))

            # now open outputfile and test stuff
            test = TextPlinkIO(
                mapfile=str(outfile),
                pedfile=str(DATA_DIR / "plinktest.ped"))
            test.read_mapfile()

            # one snp cannot be mapped
            self.assertEqual(len(test.mapdata), 3)

            for record in test.mapdata:
                variant = VariantSheep.objects(name=record.name).get()
                location = variant.get_location(version="Oar_v3.1")
                self.assertEqual(location.chrom, record.chrom)
                self.assertEqual(location.position, record.position)

        # directory and contents have been removed


if __name__ == '__main__':
    unittest.main()
