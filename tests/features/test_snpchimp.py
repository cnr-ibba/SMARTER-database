#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 13:59:34 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import types
import pathlib
import unittest

from src.features.snpchimp import read_snpChimp

FEATURE_DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"


class ReadSnpchimpTest(unittest.TestCase):
    data_path = FEATURE_DATA_DIR / "snpchimp.csv"

    def test_read_snpChimp(self):
        iterator = read_snpChimp(self.data_path)

        self.assertIsInstance(iterator, types.GeneratorType)

        test = next(iterator)
        self.assertEqual(test.snp_name, '250506CS3900065000002_1238.1')
