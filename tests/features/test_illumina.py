#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  3 17:09:17 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import pathlib
import unittest
import types

from src.features.illumina import read_snpMap, read_snpChip, read_snpList

FEATURE_DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"
SCRIPTS_DATA_DIR = pathlib.Path(__file__).parents[1] / "data/data"


class IlluminaMixin():
    data_path = None
    snp_name = None
    delimiter = None

    def read_func(self, *args, **kwargs):
        raise NotImplementedError("Please set this in child classes")

    def common(self, iterator):
        self.assertIsInstance(iterator, types.GeneratorType)

        test = next(iterator)
        self.assertEqual(test.name, self.snp_name)

    def test_read(self):
        iterator = self.read_func(path=self.data_path)
        self.common(iterator)

    def test_read_skip(self):
        iterator = self.read_func(path=self.data_path, skip=2)
        self.common(iterator)

    def test_read_delimiter(self):
        iterator = self.read_func(
            path=self.data_path, delimiter=self.delimiter)
        self.common(iterator)


class ReadSNPMapTest(IlluminaMixin, unittest.TestCase):
    data_path = FEATURE_DATA_DIR / "illumina_snpmap.txt"
    snp_name = "250506CS3900065000002_1238.1"
    delimiter = "\t"

    def read_func(self, *args, **kwargs):
        return read_snpMap(*args, **kwargs)


class ReadManifest(IlluminaMixin, unittest.TestCase):
    data_path = SCRIPTS_DATA_DIR / "test_manifest.csv"
    snp_name = "250506CS3900065000002_1238.1"
    delimiter = ","

    def read_func(self, *args, **kwargs):
        return read_snpChip(*args, **kwargs)


class ReadSnpListTest(IlluminaMixin, unittest.TestCase):
    data_path = FEATURE_DATA_DIR / "snplist.txt"
    snp_name = "250506CS3900140500001_312.1"
    delimiter = "\t"

    def read_func(self, *args, **kwargs):
        return read_snpList(*args, **kwargs)


if __name__ == '__main__':
    unittest.main()
