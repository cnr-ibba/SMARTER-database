#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 11 11:56:29 2023

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import logging
import unittest
import pathlib

from click.testing import CliRunner
from mongoengine import QuerySet

from src.data.import_dbsnp import (
    main as import_dbsnp, search_variant, process_variant)

from src.features.smarterdb import VariantSheep, Location
from src.features.dbsnp import read_dbSNP

from ..common import MongoMockMixin, VariantSheepMixin, SupportedChipMixin

import src.data.import_dbsnp

DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"
src.data.import_dbsnp.logger.setLevel(logging.INFO)


class DBSNPTestMixin(VariantSheepMixin, SupportedChipMixin, MongoMockMixin):
    # a different fixture file to load in VariantMixin
    variant_fixture = "dbsnp_sheep_variants.json"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # collect the first SNP using helper libraries
        dbsnp_file = DATA_DIR / "ds_test.xml"
        cls.snp = next(read_dbSNP(dbsnp_file))

    def setUp(self):
        super().setUp()

        self.variant = VariantSheep.objects.get(
            name="DU170943_581.1")


class VariantTest(DBSNPTestMixin, unittest.TestCase):

    def test_search_variant(self):
        # define input parameters
        sss = self.snp['ss']
        rs_id = f"rs{self.snp['rsId']}"
        locSnpIds = set([ss['locSnpId'] for ss in sss])

        # collect variant
        variants = search_variant(sss, rs_id, locSnpIds, VariantSheep)

        self.assertIsInstance(variants, QuerySet)
        self.assertEqual(variants.count(), 1)

        test = variants[0]
        self.assertEqual(test, self.variant)

    def test_process_variant(self):
        location = process_variant(
            self.snp,
            self.variant,
            supported_chips=[self.chip_name]
        )

        self.assertIsInstance(location, Location)

        reference = {
            'ss_id': 'ss836318739',
            'version': 'Oar_v4.0',
            'chrom': '24',
            'position': 33913078,
            'alleles': 'G/T',
            'illumina': 'T/G',
            'illumina_strand': 'bottom',
            'strand': 'forward',
            'imported_from': 'dbSNP151'
        }

        test = json.loads(location.to_json())
        self.assertEqual(reference, test)


class ImportDBSNPTest(DBSNPTestMixin, unittest.TestCase):

    # the function I want to test
    main_function = import_dbsnp

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()
        self.version = "Oar_v4.0"
        self.sender = "AGR_BS"

        self.variant = VariantSheep.objects.get(
            name="DU170943_581.1")

    def test_help(self):
        result = self.runner.invoke(self.main_function, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    def test_import_dbsnp(self):
        dbsnp_file = DATA_DIR / "ds_test.xml"

        result = self.runner.invoke(
            self.main_function,
            [
                "--species_class",
                "Sheep",
                "--input",
                str(dbsnp_file),
                "--sender",
                self.sender,
            ]
        )

        self.assertEqual(0, result.exit_code, msg=result.exc_info)

        # get first inserted object
        self.variant.reload()
        location = self.variant.get_location(
            version=self.version,
            imported_from='dbSNP151')

        self.assertEqual(location.chrom, "24")
        self.assertEqual(location.position, 33913078)
        self.assertEqual(location.illumina_top, "A/C")


if __name__ == '__main__':
    unittest.main()
