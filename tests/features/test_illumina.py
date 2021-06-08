#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  3 17:09:17 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import pathlib
import unittest
import types
import datetime

from src.features.illumina import (
    read_snpMap, read_Manifest, read_snpList, read_illuminaRow, skip_lines,
    skip_until_section, search_manifactured_date)

FEATURE_DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"
SCRIPTS_DATA_DIR = pathlib.Path(__file__).parents[1] / "data/data"


class SkipTest(unittest.TestCase):
    data_path = SCRIPTS_DATA_DIR / "test_manifest.csv"

    def test_skip_lines(self):
        reference = [
            "Illumina, Inc.,,,,,,,,,,,,,,,,,,,",
            "[Heading],,,,,,,,,,,,,,,,,,,,",
            "Descriptor File Name,OvineSNP50_B.bpm,,,,,,,,,,,,,,,,,,,",
            "Assay Format,Infinium HD Ultra,,,,,,,,,,,,,,,,,,,",
            "Date Manufactured,1/7/2009,,,,,,,,,,,,,,,,,,,",
            "Loci Count ,54241,,,,,,,,,,,,,,,,,,,",
            "[Assay],,,,,,,,,,,,,,,,,,,,",
        ]
        with open(self.data_path) as handle:
            _, skipped = skip_lines(handle, skip=7)

        self.assertListEqual(skipped, reference)

    def test_skip_until_section(self):
        reference = [
            "Illumina, Inc.,,,,,,,,,,,,,,,,,,,",
            "[Heading],,,,,,,,,,,,,,,,,,,,",
            "Descriptor File Name,OvineSNP50_B.bpm,,,,,,,,,,,,,,,,,,,",
            "Assay Format,Infinium HD Ultra,,,,,,,,,,,,,,,,,,,",
            "Date Manufactured,1/7/2009,,,,,,,,,,,,,,,,,,,",
            "Loci Count ,54241,,,,,,,,,,,,,,,,,,,",
            "[Assay],,,,,,,,,,,,,,,,,,,,",
        ]
        with open(self.data_path) as handle:
            _, skipped = skip_until_section(handle, "[Assay]")

        self.assertListEqual(skipped, reference)

    def test_search_manifactured_date(self):
        with open(self.data_path) as handle:
            _, skipped = skip_until_section(handle, "[Assay]")

        test = search_manifactured_date(skipped)
        reference = datetime.datetime(2009, 1, 7)

        self.assertEqual(reference, test)


class IlluminaMixin():
    data_path = None
    snp_name = None
    delimiter = None
    skip_lines = 2

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
        iterator = self.read_func(path=self.data_path, skip=self.skip_lines)
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
    skip_lines = 7

    def read_func(self, *args, **kwargs):
        return read_Manifest(*args, **kwargs)


class ReadSnpListTest(IlluminaMixin, unittest.TestCase):
    data_path = FEATURE_DATA_DIR / "snplist.txt"
    snp_name = "250506CS3900140500001_312.1"
    delimiter = "\t"

    def read_func(self, *args, **kwargs):
        return read_snpList(*args, **kwargs)


class ReadIlluminaRowTest(unittest.TestCase):
    data_path = FEATURE_DATA_DIR / "finalreport.txt"
    snp_name = "250506CS3900140500001_312.1"

    def test_read(self):
        iterator = self.read_func(path=self.data_path)
        self.assertIsInstance(iterator, types.GeneratorType)

        test = next(iterator)
        self.assertEqual(test.snp_name, self.snp_name)

    def read_func(self, *args, **kwargs):
        return read_illuminaRow(*args, **kwargs)


if __name__ == '__main__':
    unittest.main()
