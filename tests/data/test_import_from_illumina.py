#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 14 17:33:22 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import tempfile

from click.testing import CliRunner
from unittest.mock import patch, PropertyMock
from plinkio import plinkfile

from src.data.import_from_illumina import main as import_from_illumina
from src.features.smarterdb import SampleSheep, Dataset, Breed

from ..common import (
    MongoMockMixin, SmarterIDMixin, VariantsMixin, SupportedChipMixin)

DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"


class TestImportFromIllumina(
        VariantsMixin, SmarterIDMixin, SupportedChipMixin, MongoMockMixin,
        unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        # need to delete object from db after import
        SampleSheep.objects.delete()

        super().tearDownClass()

    def setUp(self):
        self.runner = CliRunner()
        self.snpfile = DATA_DIR / "snplist.txt"
        self.report = DATA_DIR / "finalreport.txt"
        self.dataset = Dataset.objects.get(file="test.zip")

    def link_files(self, working_dir):
        snpfile = working_dir / "snplist.txt"
        report = working_dir / "finalreport.txt"

        snpfile.symlink_to(self.snpfile)
        report.symlink_to(self.report)

    def test_help(self):
        result = self.runner.invoke(import_from_illumina, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_illumina(self, my_working_dir, my_result_dir):
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
                import_from_illumina,
                [
                    "--dataset",
                    "test.zip",
                    "--snpfile",
                    "snplist.txt",
                    "--report",
                    "finalreport.txt",
                    "--breed_code",
                    "TEX",
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

            plink_path = results_dir / "OAR3" / "finalreport_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 2)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_illumina_no_fid(self, my_working_dir, my_result_dir):
        """Search breed relying on database"""

        # create two fake samples to colled fid relying on database
        sample = SampleSheep(
            original_id="1",
            country="Italy",
            breed="Texel",
            breed_code="TEX",
            dataset=self.dataset,
            type_="background",
            chip_name=self.chip_name
        )
        sample.save()

        sample = SampleSheep(
            original_id="2",
            country="Italy",
            breed="Merino",
            breed_code="MER",
            dataset=self.dataset,
            type_="background",
            chip_name=self.chip_name
        )
        sample.save()

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
                import_from_illumina,
                [
                    "--dataset",
                    "test.zip",
                    "--snpfile",
                    "snplist.txt",
                    "--report",
                    "finalreport.txt",
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

            plink_path = results_dir / "OAR3" / "finalreport_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 2)

            # assert two different FID for samples
            for record in sample_list:
                sample = SampleSheep.objects.get(smarter_id=record.iid)
                self.assertEqual(sample.breed_code, record.fid)

    @patch('src.features.plinkio.SmarterMixin.fetch_coordinates')
    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_skip(self, my_working_dir, my_result_dir, my_fetch):
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
            plink_prefix = plink_path / "finalreport_updated"

            bedfile = plink_prefix.with_suffix(".bed")
            bimfile = plink_prefix.with_suffix(".bim")
            famfile = plink_prefix.with_suffix(".fam")

            bedfile.symlink_to(DATA_DIR / "plinktest.bed")
            bimfile.symlink_to(DATA_DIR / "plinktest.bim")
            famfile.symlink_to(DATA_DIR / "plinktest.fam")

            result = self.runner.invoke(
                import_from_illumina,
                [
                    "--dataset",
                    "test.zip",
                    "--snpfile",
                    "snplist.txt",
                    "--report",
                    "finalreport.txt",
                    "--breed_code",
                    "TEX",
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
