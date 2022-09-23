#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 14:05:10 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib

from click.testing import CliRunner

from src.data.import_snpchimp import main as import_snpchimp
from src.features.smarterdb import VariantSheep

from ..common import MongoMockMixin, VariantsMixin

DATA_DIR = pathlib.Path(__file__).parent / "data"


class ImportSNPChimpTest(VariantsMixin, MongoMockMixin, unittest.TestCase):
    main_function = import_snpchimp

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()
        self.version = "Oar_v4.0"

        self.variant = VariantSheep.objects.get(
            name="250506CS3900065000002_1238.1")

    def import_data(self):
        snpchimp_file = DATA_DIR / "test_snpchimp.csv"

        result = self.runner.invoke(
            self.main_function,
            [
                "--species_class",
                "Sheep",
                "--snpchimp",
                str(snpchimp_file),
                "--version",
                self.version,
            ]
        )

        self.assertEqual(0, result.exit_code, msg=result.exc_info)

    def test_help(self):
        result = self.runner.invoke(self.main_function, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    def test_import_snpchimp(self):
        self.import_data()

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='SNPchiMp v.3')

        self.assertEqual(location.chrom, "15")
        self.assertEqual(location.position, 5859890)
        self.assertEqual(location.illumina_top, "A/G")

    def test_import_snpchimp_update_rs(self):
        self.variant.rs_id = None
        self.variant.save()

        self.import_data()

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='SNPchiMp v.3')

        self.assertEqual(location.chrom, "15")
        self.assertEqual(location.position, 5859890)
        self.assertEqual(location.illumina_top, "A/G")
        self.assertEqual(self.variant.rs_id, ["rs55630613"])

    def test_import_snpchimp_clean_chrom(self):
        self.import_data()

        # get an unmapped variant
        variant = VariantSheep.objects.get(
            name="250506CS3900435700001_1658.1")

        location = variant.get_location(
            version=self.version,
            imported_from='SNPchiMp v.3')

        self.assertEqual(location.chrom, "0")
        self.assertEqual(location.position, 0)
        self.assertEqual(location.illumina_top, "A/G")
