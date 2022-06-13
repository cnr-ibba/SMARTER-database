#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 16:39:57 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import types
import pathlib
import unittest
import datetime

from src.features.affymetrix import (
    search_manifactured_date, read_Manifest, skip_comments)

SCRIPTS_DATA_DIR = pathlib.Path(__file__).parents[1] / "data/data"


class ReadManifest(unittest.TestCase):
    data_path = SCRIPTS_DATA_DIR / "test_affy.csv"

    def test_skip_comments(self):
        with open(self.data_path) as handle:
            position, skipped = skip_comments(handle)
            self.assertEqual(len(skipped), 20)

    def test_search_manifactured_date(self):
        data = ['#%create_date=2019-01-17 GMT-08:00 12:04:49']
        test = search_manifactured_date(data)
        reference = datetime.datetime(2019, 1, 17, 12, 4, 49)

        self.assertEqual(reference, test)

        data = ['#%create_date=Tue Apr  4 11:40:20 2017']
        test = search_manifactured_date(data)
        reference = datetime.datetime(2017, 4, 4, 11, 40, 20)

        self.assertEqual(reference, test)

    def test_readManifest(self):
        iterator = read_Manifest(self.data_path)

        self.assertIsInstance(iterator, types.GeneratorType)

        test = next(iterator)
        self.assertEqual(test.cust_id, '250506CS3900176800001_906_01')
