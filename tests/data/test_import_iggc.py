#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 15:01:53 2023

@author: Paolo Cozzi <bunop@libero.it>
"""

import unittest
import pathlib
import datetime

from click.testing import CliRunner

from src.data.import_iggc import (
    main as import_consortium, check_strand)
from src.features.smarterdb import VariantGoat, Location, SmarterDBException

from ..common import MongoMockMixin, VariantGoatMixin

DATA_DIR = pathlib.Path(__file__).parent / "data"


class ConsortiumMixin(VariantGoatMixin, MongoMockMixin):
    main_function = import_consortium

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()
        self.version = "ARS1"

        self.variant = VariantGoat.objects.get(
            name="snp1-scaffold1-2170")

    def import_data(self, *args):
        data_file = DATA_DIR / "test_iggc.csv"

        result = self.runner.invoke(
            self.main_function,
            [
                "--datafile",
                str(data_file),
                "--version",
                self.version,
                "--chrom_column",
                "ars1_chr",
                "--pos_column",
                "ars1_pos",
                "--strand_column",
                "ars1_strand"
            ] + list(args)
        )

        self.assertEqual(0, result.exit_code, msg=result.exc_info)


class ImportConsortiumTest(ConsortiumMixin, unittest.TestCase):

    def test_help(self):
        result = self.runner.invoke(self.main_function, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    def test_import_consortium(self):
        self.import_data()

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='consortium')

        self.assertEqual(location.chrom, "22")
        self.assertEqual(location.position, 27303588)
        self.assertEqual(location.illumina_top, "A/C")

    def test_check_strand(self):
        self.assertEqual(check_strand("-"), "reverse")
        self.assertEqual(check_strand("+"), "forward")
        self.assertIsNone(check_strand("meow"))


class ConsortiumUpdateTest(ConsortiumMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

        # add a custom location object
        location = Location(**{
            "version": "ARS1",
            "chrom": "meow",
            "position": 27303588,
            "illumina": "A/C",
            "illumina_strand": "TOP",
            "imported_from": "consortium"
        })

        self.variant.locations.append(location)
        self.variant.save()

    def tearDown(self):
        try:
            index = self.variant.get_location_index(
                version=self.version,
                imported_from='consortium')

            del(self.variant.locations[index])
            self.variant.save()

        except SmarterDBException:
            pass

    def test_no_update(self):
        self.import_data()

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='consortium')

        self.assertEqual(location.chrom, "meow")
        self.assertEqual(location.position, 27303588)
        self.assertEqual(location.illumina_top, "A/C")

    def test_force_update(self):
        self.import_data("--force_update")

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='consortium')

        self.assertEqual(location.chrom, "22")
        self.assertEqual(location.position, 27303588)
        self.assertEqual(location.illumina_top, "A/C")

    def test_update_time(self):
        self.import_data("--force_update", "--date", "20230420")

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='consortium')

        self.assertEqual(location.chrom, "22")
        self.assertEqual(location.position, 27303588)
        self.assertEqual(location.illumina_top, "A/C")
        self.assertEqual(location.date, datetime.datetime(2023, 4, 20, 0, 0))


if __name__ == '__main__':
    unittest.main()
