#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 17:32:28 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import unittest
import pathlib

from src.features.smarterdb import global_connection, VariantSheep, Location

# set global connection
global_connection("test")

# set data dir (like os.dirname(__file__)) + "fixtures"
DATA_DIR = pathlib.Path(__file__).parent / "fixtures"


class VariantSheepTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DATA_DIR / "variant.json") as handle:
            cls.data = json.load(handle)

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
            Exception,
            "Couldn't determine a unique location for",
            self.variant.get_location,
            version="Oar_v4.0",
            imported_from='SNPchiMp v.3'
        )


if __name__ == '__main__':
    unittest.main()
