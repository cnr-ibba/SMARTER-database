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

from src.data.import_affymetrix import (
    main as import_affymetrix, search_database)
from src.features.affymetrix import read_Manifest
from src.features.smarterdb import VariantSheep, SupportedChip, Probeset

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

        # custom attributes
        cls.version = "Oar_v3.1"
        cls.manifest_file = DATA_DIR / "test_affy.csv"

        # read manifest data
        cls.manifest_data = list(read_Manifest(cls.manifest_file))

    def import_data(self):
        """import affy data after defining import function"""

        result = self.runner.invoke(
            self.main_function,
            [
                "--species_class",
                "Sheep",
                "--manifest",
                str(self.manifest_file),
                "--chip_name",
                self.chip_name,
                "--version",
                self.version,
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

        # test probeset
        probeset = next(
            filter(
                lambda probeset: probeset.chip_name == 'AffymetrixAxiomOviCan',
                test.probesets
            )
        )
        self.assertIn('AX-124359447', probeset.probeset_id)

        self.assertEqual(test.affy_snp_id, "Affx-122835222")
        self.assertIn(self.chip_name, test.sequence)
        self.assertEqual(test.cust_id, "250506CS3900176800001_906_01")
        self.assertEqual(location.chrom, "7")
        self.assertEqual(location.position, 81590897)
        self.assertEqual(location.illumina_top, "A/G")
        self.assertEqual(location.affymetrix_ab, "T/C")
        self.assertEqual(location.alleles, "C/T")
        self.assertEqual(
            location.date,
            datetime.datetime(2019, 1, 17, 12, 4, 49))


class UpdateManifestTest(
        ManifestMixin, SupportedChipMixin, VariantsMixin, MongoMockMixin,
        unittest.TestCase):

    """test import with already loaded data"""

    main_function = import_affymetrix

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()

        self.chip.n_of_snps = 0
        self.chip.save()

        # assign a fake probeset id to a variant. Test updating list
        variant = VariantSheep.objects.get(name="250506CS3900176800001_906.1")
        variant.probesets = [
            Probeset(chip_name='AffymetrixAxiomOviCan', probeset_id=["test"])]
        variant.save()

    def test_import_manifest(self):
        """test update illumina data with affymetrix"""
        self.import_data()

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

        # test probeset
        probeset = next(
            filter(
                lambda probeset: probeset.chip_name == 'AffymetrixAxiomOviCan',
                test.probesets
            )
        )
        self.assertIn('test', probeset.probeset_id)
        self.assertIn('AX-124359447', probeset.probeset_id)

        self.assertEqual(test.affy_snp_id, "Affx-122835222")
        self.assertEqual(len(test.sequence), 3)
        self.assertIn('IlluminaOvineSNP50', test.sequence)
        self.assertIn('IlluminaOvineHDSNP', test.sequence)
        self.assertIn(self.chip_name, test.sequence)
        self.assertEqual(test.cust_id, "250506CS3900176800001_906_01")

        # test an updated location
        location = test.get_location(
            version="Oar_v3.1",
            imported_from="affymetrix")

        self.assertEqual(location.illumina_top, "A/G")

        # this is only affymetrix
        test = VariantSheep.objects.get(name="Affx-293815543")

        self.assertEqual(test.name, "Affx-293815543")
        self.assertEqual(test.chip_name, [self.chip_name])

        # test probeset
        probeset = next(
            filter(
                lambda probeset: probeset.chip_name == 'AffymetrixAxiomOviCan',
                test.probesets
            )
        )
        self.assertIn('AX-104088695', probeset.probeset_id)

        self.assertEqual(test.affy_snp_id, "Affx-293815543")
        self.assertEqual(len(test.sequence), 1)
        self.assertIn(self.chip_name, test.sequence)
        self.assertIsNone(test.cust_id)

        # test updated location
        location = test.get_location(
            version="Oar_v3.1",
            imported_from="affymetrix")

        self.assertEqual(location.illumina_top, "A/G")

    def test_import_manifest_not_mapped(self):
        self.import_data()

        # get an unmapped variant
        variant = VariantSheep.objects.get(
            name="250506CS3900435700001_1658.1")

        location = variant.get_location(
            version=self.version,
            imported_from='affymetrix')

        self.assertEqual(location.chrom, "0")
        self.assertEqual(location.position, 0)
        self.assertEqual(location.illumina_top, "A/G")

    def test_search_database(self):
        """Test getting snp while updating manifest"""

        self.import_data()

        # get a snp available only in affymetrix manifest
        record = self.manifest_data[1]
        qs = search_database(record, VariantSheep)

        self.assertEqual(qs.count(), 1)
        variant = qs.get()
        self.assertEqual(variant.name, record.affy_snp_id)


if __name__ == '__main__':
    unittest.main()
