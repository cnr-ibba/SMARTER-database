#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 15:03:30 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import tempfile

from click.testing import CliRunner
from unittest.mock import patch, PropertyMock
from plinkio import plinkfile

from src.data.import_from_plink import main as import_from_plink
from src.features.smarterdb import SampleSheep, get_or_create_sample

from ..common import (
    MongoMockMixin, SmarterIDMixin, VariantSheepMixin, SupportedChipMixin)

DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"


class TestImportFromPlink(
        VariantSheepMixin, SmarterIDMixin, SupportedChipMixin, MongoMockMixin,
        unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        # need to delete object from db after import
        SampleSheep.objects.delete()

        super().tearDownClass()

    def setUp(self):
        self.runner = CliRunner()

        self.mapfile = DATA_DIR / "plinktest.map"
        self.pedfile = DATA_DIR / "plinktest.ped"
        self.bedfile = DATA_DIR / "plinktest.bed"
        self.bimfile = DATA_DIR / "plinktest.bim"
        self.famfile = DATA_DIR / "plinktest.fam"

    def link_files(self, working_dir):
        mapfile = working_dir / "plinktest.map"
        pedfile = working_dir / "plinktest.ped"
        bedfile = working_dir / "plinktest.bed"
        bimfile = working_dir / "plinktest.bim"
        famfile = working_dir / "plinktest.fam"

        mapfile.symlink_to(self.mapfile)
        pedfile.symlink_to(self.pedfile)
        bedfile.symlink_to(self.bedfile)
        bimfile.symlink_to(self.bimfile)
        famfile.symlink_to(self.famfile)

    def test_help(self):
        result = self.runner.invoke(import_from_plink, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_text_plink(self, my_working_dir, my_result_dir):
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
                import_from_plink,
                [
                    "--dataset",
                    "test.zip",
                    "--file",
                    "plinktest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR3",
                    "--create_samples"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(SampleSheep.objects.count(), 2)

            # check imported chip_name attribute
            for sample in SampleSheep.objects:
                self.assertEqual(sample.chip_name, self.chip_name)

            plink_path = results_dir / "OAR3" / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_plink_alias(self, my_working_dir, my_result_dir):
        """Simulate an import using alias for sample names"""

        # ok, create two fake samples with alias and a custom original_id
        for i in range(1, 3):
            get_or_create_sample(
                SampleSheep,
                original_id=f"custom_{i}",
                dataset=self.dataset,
                type_="foreground",
                breed=self.breed,
                country="Italy",
                species="Ovis aries",
                chip_name=self.chip_name,
                alias=i)

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
                import_from_plink,
                [
                    "--dataset",
                    "test.zip",
                    "--file",
                    "plinktest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR3",
                    "--sample_field",
                    "alias"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(SampleSheep.objects.count(), 2)

            # check imported chip_name attribute
            for sample in SampleSheep.objects:
                self.assertEqual(sample.chip_name, self.chip_name)

            plink_path = results_dir / "OAR3" / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_text_plink_src_assembly(
            self, my_working_dir, my_result_dir):
        """Test import from plink using a source assembly"""

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
                import_from_plink,
                [
                    "--dataset",
                    "test.zip",
                    "--file",
                    "plinktest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR4",
                    "--create_samples",
                    "--src_version",
                    "Oar_v3.1",
                    "--src_imported_from",
                    "manifest"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(SampleSheep.objects.count(), 2)

            # check imported chip_name attribute
            for sample in SampleSheep.objects:
                self.assertEqual(sample.chip_name, self.chip_name)

            plink_path = results_dir / "OAR4" / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_text_plink_by_positions(
            self, my_working_dir, my_result_dir):
        """Test import from plink using positions"""

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
                import_from_plink,
                [
                    "--dataset",
                    "test.zip",
                    "--file",
                    "plinktest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR4",
                    "--create_samples",
                    "--src_version",
                    "Oar_v3.1",
                    "--src_imported_from",
                    "manifest",
                    "--search_by_positions"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(SampleSheep.objects.count(), 2)

            # check imported chip_name attribute
            for sample in SampleSheep.objects:
                self.assertEqual(sample.chip_name, self.chip_name)

            plink_path = results_dir / "OAR4" / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_text_plink_ignore_coding(
            self, my_working_dir, my_result_dir):
        """Test import from plink ignoring coding check"""

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
                import_from_plink,
                [
                    "--dataset",
                    "test.zip",
                    "--file",
                    "plinktest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR3",
                    "--create_samples",
                    "--src_coding",
                    "forward",
                    "--ignore_coding_errors"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(SampleSheep.objects.count(), 2)

            # check imported chip_name attribute
            for sample in SampleSheep.objects:
                self.assertEqual(sample.chip_name, self.chip_name)

            plink_path = results_dir / "OAR3" / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_binary_plink(self, my_working_dir, my_result_dir):
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
                import_from_plink,
                [
                    "--dataset",
                    "test.zip",
                    "--bfile",
                    "plinktest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR3",
                    "--create_samples"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(SampleSheep.objects.count(), 2)

            # check imported chip_name attribute
            for sample in SampleSheep.objects:
                self.assertEqual(sample.chip_name, self.chip_name)

            plink_path = results_dir / "OAR3" / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_mutually_exclusive_options(self, my_working_dir, my_result_dir):
        """--file and -bfile options are mutually exclusive"""

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
                import_from_plink,
                [
                    "--dataset",
                    "test.zip",
                    "--file",
                    "plinktest",
                    "--bfile",
                    "plinktest"
                    "--assembly",
                    "OAR3",
                    "--create_samples"
                ]
            )

            self.assertEqual(2, result.exit_code)

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
            plink_prefix = plink_path / "plinktest_updated"

            bedfile = plink_prefix.with_suffix(".bed")
            bimfile = plink_prefix.with_suffix(".bim")
            famfile = plink_prefix.with_suffix(".fam")

            bedfile.symlink_to(self.bedfile)
            bimfile.symlink_to(self.bimfile)
            famfile.symlink_to(self.famfile)

            result = self.runner.invoke(
                import_from_plink,
                [
                    "--dataset",
                    "test.zip",
                    "--bfile",
                    "plinktest",
                    "--chip_name",
                    self.chip_name,
                    "--assembly",
                    "OAR3",
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
