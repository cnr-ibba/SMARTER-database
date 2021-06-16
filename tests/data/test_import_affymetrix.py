#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 15:44:58 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import datetime

from click.testing import CliRunner

from src.data.import_affymetrix import main as import_affymetrix
from src.features.smarterdb import VariantSheep, SupportedChip

from ..common import MongoMockMixin, VariantsMixin, SupportedChipMixin

DATA_DIR = pathlib.Path(__file__).parent / "data"


class ManifestMixin():
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # add a new custom chip
        cls.chip_name = "AffymetrixAxiomOviCan"
        cls.chip = SupportedChip(name=cls.chip_name, species="Sheep")
        cls.chip.save()

    def import_data(self):
        manifest_file = DATA_DIR / "test_affy.db"

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
            ]
        )

        self.assertEqual(0, result.exit_code, msg=result.exc_info)


class ImportManifestTest(
        ManifestMixin, SupportedChipMixin, MongoMockMixin, unittest.TestCase):

    main_function = import_affymetrix

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
        self.assertEqual(self.chip.n_of_snps, 3)

        # get first inserted object
        test = VariantSheep.objects.first()
        location = test.locations[0]

        # test inserted fields for first object
        self.assertEqual(test.name, "Affx-122835222")
        self.assertEqual(test.chip_name, [self.chip_name])
        self.assertEqual(test.probeset_id, ["AX-124359447"])
        self.assertEqual(test.affy_snp_id, "Affx-122835222")
        self.assertIn('affymetrix', test.sequence)
        self.assertEqual(test.cust_id, "250506CS3900176800001_906_01")
        self.assertEqual(location.chrom, "7")
        self.assertEqual(location.position, 81590897)
        self.assertEqual(location.illumina_top, "A/G")
        self.assertEqual(location.affymetrix_ab, "T/C")
        self.assertEqual(location.alleles, "C/T")
        self.assertEqual(location.date, datetime.datetime(2018, 12, 17))


class UpdateManifestTest(
        ManifestMixin, SupportedChipMixin, VariantsMixin, MongoMockMixin,
        unittest.TestCase):

    main_function = import_affymetrix

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()

        self.chip.n_of_snps = 0
        self.chip.save()

        # assign a fake probeset id to a variant. Test updating list
        variant = VariantSheep.objects.get(name="250506CS3900176800001_906.1")
        variant.probeset_id = ["test"]
        variant.save()

    def test_import_manifest(self):
        """test update illumina data with affymetrix"""
        self.import_data()

        # affychip should report 2 snps
        self.chip.reload()
        self.assertEqual(self.chip.n_of_snps, 3)

        # should have 4 variant in total, 2 illumina, 2 both, 1 affymetrix
        self.assertEqual(VariantSheep.objects.count(), 5)

        # get the variation in common from two manifacturers
        test = VariantSheep.objects.get(name="250506CS3900176800001_906.1")

        self.assertEqual(test.name, "250506CS3900176800001_906.1")
        self.assertEqual(test.chip_name, [
            "IlluminaOvineSNP50",
            "IlluminaOvineHDSNP",
            self.chip_name
        ])
        self.assertEqual(test.probeset_id, ["test", "AX-124359447"])
        self.assertEqual(test.affy_snp_id, "Affx-122835222")
        self.assertIn('illumina', test.sequence)
        self.assertIn('affymetrix', test.sequence)
        self.assertEqual(test.cust_id, "250506CS3900176800001_906_01")

        # test updated location
        location = test.get_location(
            version="Oar_v3.1",
            imported_from="affymetrix")

        self.assertEqual(location.illumina_top, "A/G")

        # this is only affymetrix
        test = VariantSheep.objects.get(name="Affx-293815543")

        self.assertEqual(test.name, "Affx-293815543")
        self.assertEqual(test.chip_name, [self.chip_name])
        self.assertEqual(test.probeset_id, ["AX-104088695"])
        self.assertEqual(test.affy_snp_id, "Affx-293815543")
        self.assertNotIn('illumina', test.sequence)
        self.assertIn('affymetrix', test.sequence)
        self.assertIsNone(test.cust_id)

        # test updated location
        location = test.get_location(
            version="Oar_v3.1",
            imported_from="affymetrix")

        self.assertEqual(location.illumina_top, "A/G")
