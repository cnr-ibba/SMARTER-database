#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 12:22:12 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import datetime

from click.testing import CliRunner

from src.data.import_manifest import main as import_manifest
from src.features.smarterdb import VariantSheep

from ..common import MongoMockMixin, VariantsMixin, SupportedChipMixin

DATA_DIR = pathlib.Path(__file__).parent / "data"


class ManifestMixin():
    def import_data(self):
        manifest_file = DATA_DIR / "test_manifest.csv"

        result = self.runner.invoke(
            self.main_function,
            [
                "--species",
                "Sheep",
                "--manifest",
                str(manifest_file),
                "--chip_name",
                self.chip_name,
                "--version",
                "Oar_v3.1",
                "--sender",
                "AGR_BS"
            ]
        )

        self.assertEqual(0, result.exit_code, msg=result.exception)


class ImportManifestTest(
        ManifestMixin, SupportedChipMixin, MongoMockMixin, unittest.TestCase):

    main_function = import_manifest

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()

        self.chip.n_of_snps = 0
        self.chip.save()

    def tearDown(self):
        VariantSheep.objects.delete()

        super().tearDown()

    # HINT: move to a common Mixin?
    def test_help(self):
        result = self.runner.invoke(self.main_function, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    def test_import_manifest(self):
        self.import_data()

        self.chip.reload()
        self.assertEqual(self.chip.n_of_snps, 4)

        # get first inserted object
        test = VariantSheep.objects.first()
        location = test.locations[0]

        # test inserted fields for first object
        self.assertEqual(test.name, "250506CS3900065000002_1238.1")
        self.assertEqual(len(test.sequence), 1)
        self.assertIn(self.chip_name, test.sequence)
        self.assertEqual(location.chrom, "15")
        self.assertEqual(location.position, 5870057)
        self.assertEqual(location.illumina_top, "A/G")
        self.assertEqual(location.date, datetime.datetime(2009, 1, 7))


class UpdateManifestTest(
        ManifestMixin, SupportedChipMixin, VariantsMixin, MongoMockMixin,
        unittest.TestCase):

    main_function = import_manifest

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()

        self.chip.n_of_snps = 3
        self.chip.save()

        # changing variants chip name
        VariantSheep.objects.update(chip_name=["test"])

    def test_update_chip_name(self):
        self.import_data()

        # testing two chips names
        for variant in VariantSheep.objects():
            self.assertIsInstance(variant.chip_name, list)
            self.assertEqual(variant.chip_name, ["test", self.chip_name])
