#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 14:27:19 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import tempfile

from click.testing import CliRunner
from unittest.mock import patch, PropertyMock
from plinkio import plinkfile

from src.data.import_from_affymetrix import main as import_from_affymetrix
from src.features.smarterdb import SampleSheep, Dataset

from ..common import (
    MongoMockMixin, SmarterIDMixin, VariantsMixin, SupportedChipMixin)

DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"


class TestImportFromAffymetrix(
        VariantsMixin, SmarterIDMixin, SupportedChipMixin, MongoMockMixin,
        unittest.TestCase):

    # a different fixture file to load in VariantMixin
    variant_fixture = "affy_variants.json"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.dataset = Dataset.objects.get(file="test.zip")

    @classmethod
    def tearDownClass(cls):
        # need to delete object from db after import
        SampleSheep.objects.delete()

        super().tearDownClass()

    def setUp(self):
        self.runner = CliRunner()
        self.mapfile = DATA_DIR / "affytest.map"
        self.pedfile = DATA_DIR / "affytest.ped"

    def link_files(self, working_dir):
        mapfile = working_dir / "affytest.map"
        pedfile = working_dir / "affytest.ped"

        mapfile.symlink_to(self.mapfile)
        pedfile.symlink_to(self.pedfile)

    def test_help(self):
        result = self.runner.invoke(import_from_affymetrix, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_affymetrix(self, my_working_dir, my_result_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # assign return value to mocked property
            my_working_dir.return_value = working_dir
            my_result_dir.return_value = results_dir

            # copy test data files
            self.link_files(working_dir)

            result = self.runner.invoke(
                import_from_affymetrix,
                [
                    "--dataset",
                    "test.zip",
                    "--file",
                    "affytest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR3",
                    "--coding",
                    "forward",
                    "--breed_code",
                    "TEX",
                    "--sample_field",
                    "alias",
                    "--create_samples"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(SampleSheep.objects.count(), 2)

            # check imported chip_name attribute
            for sample in SampleSheep.objects:
                self.assertEqual(sample.chip_name, self.chip_name)

            plink_path = results_dir / "OAR3" / "affytest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 2)

    @patch('src.features.plinkio.SmarterMixin.fetch_coordinates')
    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_skip(self, my_working_dir, my_result_dir, my_fetch):
        """test no import if output files exist"""

        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # assign return value to mocked property
            my_working_dir.return_value = working_dir
            my_result_dir.return_value = results_dir

            # copy test data files
            self.link_files(working_dir)

            # link espected output files in results dir
            plink_path = results_dir / "OAR3"
            plink_path.mkdir(parents=True, exist_ok=True)

            # this should be the input filename with _updated suffix
            plink_prefix = plink_path / "affytest_updated"

            bedfile = plink_prefix.with_suffix(".bed")
            bimfile = plink_prefix.with_suffix(".bim")
            famfile = plink_prefix.with_suffix(".fam")

            # link some binary plink files to symulate an output
            bedfile.symlink_to(DATA_DIR / "plinktest.bed")
            bimfile.symlink_to(DATA_DIR / "plinktest.bim")
            famfile.symlink_to(DATA_DIR / "plinktest.fam")

            result = self.runner.invoke(
                import_from_affymetrix,
                [
                    "--dataset",
                    "test.zip",
                    "--file",
                    "affytest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR3",
                    "--coding",
                    "forward",
                    "--breed_code",
                    "TEX",
                    "--sample_field",
                    "alias",
                    "--create_samples"
                ]
            )

            # no sample inserted (step is skipped)
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(SampleSheep.objects.count(), 0)

            # no coordinate fetch (file not processed)
            self.assertFalse(my_fetch.called)


if __name__ == '__main__':
    unittest.main()
