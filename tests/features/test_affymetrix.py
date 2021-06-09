#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 16:39:57 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import types
import sqlite3
import pathlib
import unittest
import datetime

from src.features.affymetrix import search_manifactured_date, read_Manifest

SCRIPTS_DATA_DIR = pathlib.Path(__file__).parents[1] / "data/data"


class ReadManifest(unittest.TestCase):
    data_path = SCRIPTS_DATA_DIR / "test_affy.db"

    def test_search_manifactured_date(self):
        with sqlite3.connect(self.data_path) as conn:
            curs = conn.cursor()

            test = search_manifactured_date(curs)

        reference = datetime.datetime(2018, 12, 17)

        self.assertEqual(reference, test)

    def test_readManifest(self):
        iterator = read_Manifest(self.data_path)

        self.assertIsInstance(iterator, types.GeneratorType)

        test = next(iterator)
        self.assertEqual(test.cust_id, '250506CS3900176800001_906_01')
