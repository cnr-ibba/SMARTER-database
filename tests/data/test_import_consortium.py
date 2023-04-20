#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 23 18:02:09 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import datetime

from click.testing import CliRunner

from src.data.import_consortium import (
    main as import_consortium, check_chromosomes)
from src.features.smarterdb import VariantSheep, Location, SmarterDBException

from ..common import MongoMockMixin, VariantsMixin

DATA_DIR = pathlib.Path(__file__).parent / "data"


class ConsortiumMixin(VariantsMixin, MongoMockMixin):
    main_function = import_consortium

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()
        self.version = "Oar_v3.1"

        self.variant = VariantSheep.objects.get(
            name="250506CS3900065000002_1238.1")

    def import_data(self, *args):
        data_file = DATA_DIR / "test_consortium.csv"

        result = self.runner.invoke(
            self.main_function,
            [
                "--species_class",
                "Sheep",
                "--datafile",
                str(data_file),
                "--version",
                self.version,
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

        self.assertEqual(location.chrom, "15")
        self.assertEqual(location.position, 5870057)
        self.assertEqual(location.illumina_top, "A/G")

    def test_check_chromosomes(self):
        self.assertEqual(check_chromosomes("26", "Sheep"), "26")
        self.assertEqual(check_chromosomes("27", "Sheep"), "X")
        self.assertRaises(NotImplementedError, check_chromosomes, 1, "Goat")


class ConsortiumUpdateTest(ConsortiumMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

        # add a custom location object
        location = Location(**{
            "version": "Oar_v3.1",
            "chrom": "meow",
            "position": 5870057,
            "illumina": "T/C",
            "illumina_strand": "BOT",
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
        self.assertEqual(location.position, 5870057)
        self.assertEqual(location.illumina_top, "A/G")

    def test_force_update(self):
        self.import_data("--force_update")

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='consortium')

        self.assertEqual(location.chrom, "15")
        self.assertEqual(location.position, 5870057)
        self.assertEqual(location.illumina_top, "A/G")

    def test_update_time(self):
        self.import_data("--force_update", "--date", "20230420")

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='consortium')

        self.assertEqual(location.chrom, "15")
        self.assertEqual(location.position, 5870057)
        self.assertEqual(location.illumina_top, "A/G")
        self.assertEqual(location.date, datetime.datetime(2023, 4, 20, 0, 0))
