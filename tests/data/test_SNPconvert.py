#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 15:50:29 2022

@author: Paolo Cozzi <bunop@libero.it>
"""

import unittest
import tempfile
import pathlib

from click.testing import CliRunner
from plinkio import plinkfile

from src.data.SNPconvert import main as snp_convert
from src.features.smarterdb import SmarterDBException

from ..common import (
    MongoMockMixin, VariantSheepMixin, SupportedChipMixin)

DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"


class SNPconvertTest(
        VariantSheepMixin, SupportedChipMixin, MongoMockMixin,
        unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.mapfile = DATA_DIR / "plinktest.map"
        self.pedfile = DATA_DIR / "plinktest.ped"
        self.bedfile = DATA_DIR / "plinktest.bed"
        self.bimfile = DATA_DIR / "plinktest.bim"
        self.famfile = DATA_DIR / "plinktest.fam"
        self.snpfile = DATA_DIR / "snplist.txt"
        self.snpfile_3cols = DATA_DIR / "snplist_3cols.txt"
        self.report = DATA_DIR / "finalreport.txt"

        self.main_function = snp_convert
        self.runner = CliRunner()

    def link_files(self, working_dir):
        mapfile = working_dir / "plinktest.map"
        pedfile = working_dir / "plinktest.ped"
        bedfile = working_dir / "plinktest.bed"
        bimfile = working_dir / "plinktest.bim"
        famfile = working_dir / "plinktest.fam"
        snpfile = working_dir / "snplist.txt"
        snpfile_3cols = working_dir / "snplist_3cols.txt"
        report = working_dir / "finalreport.txt"

        # create links
        mapfile.symlink_to(self.mapfile)
        pedfile.symlink_to(self.pedfile)
        bedfile.symlink_to(self.bedfile)
        bimfile.symlink_to(self.bimfile)
        famfile.symlink_to(self.famfile)
        snpfile.symlink_to(self.snpfile)
        snpfile_3cols.symlink_to(self.snpfile_3cols)
        report.symlink_to(self.report)

    def test_help(self):
        result = self.runner.invoke(self.main_function, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    def test_import_from_text_plink(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # copy test data files
            self.link_files(working_dir)

            result = self.runner.invoke(
                self.main_function,
                [
                    "--file",
                    str(working_dir / "plinktest"),
                    "--assembly",
                    "OAR3",
                    "--species",
                    "Sheep",
                    "--results_dir",
                    results_dir,
                    "--chip_name",
                    self.chip_name,
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            plink_path = results_dir / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    def test_import_from_text_plink_search_positions(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # copy test data files
            self.link_files(working_dir)

            result = self.runner.invoke(
                self.main_function,
                [
                    "--file",
                    str(working_dir / "plinktest"),
                    "--search_by_positions",
                    "--src_version",
                    "Oar_v3.1",
                    "--src_imported_from",
                    "SNPchiMp v.3",
                    "--assembly",
                    "OAR3",
                    "--species",
                    "Sheep",
                    "--results_dir",
                    results_dir,
                    "--chip_name",
                    self.chip_name,
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exc_info)

            plink_path = results_dir / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    def test_import_from_text_plink_assembly_not_managed(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # copy test data files
            self.link_files(working_dir)

            result = self.runner.invoke(
                self.main_function,
                [
                    "--file",
                    str(working_dir / "plinktest"),
                    "--assembly",
                    "OAR5",
                    "--species",
                    "Sheep",
                    "--results_dir",
                    results_dir,
                    "--chip_name",
                    self.chip_name,
                ]
            )

            self.assertEqual(1, result.exit_code, msg=result.exception)
            self.assertIsInstance(result.exception, SmarterDBException)

            plink_path = results_dir / "plinktest_updated"
            self.assertFalse(plink_path.exists())

    def test_import_from_binary_plink(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # copy test data files
            self.link_files(working_dir)

            result = self.runner.invoke(
                self.main_function,
                [
                    "--bfile",
                    str(working_dir / "plinktest"),
                    "--assembly",
                    "OAR3",
                    "--species",
                    "Sheep",
                    "--results_dir",
                    results_dir,
                    "--chip_name",
                    self.chip_name,
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            plink_path = results_dir / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)

    def test_import_from_illumina(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # copy test data files
            self.link_files(working_dir)

            result = self.runner.invoke(
                self.main_function,
                [
                    "--report",
                    str(working_dir / "finalreport.txt"),
                    "--snpfile",
                    str(working_dir / "snplist.txt"),
                    "--src_coding",
                    "ab",
                    "--assembly",
                    "OAR3",
                    "--species",
                    "Sheep",
                    "--results_dir",
                    results_dir,
                    "--chip_name",
                    self.chip_name,
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            plink_path = results_dir / "finalreport_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 2)

    def test_import_from_illumina_3_columns(self):
        """Test importing from illumina with 3 columns in SNPfile"""

        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # copy test data files
            self.link_files(working_dir)

            result = self.runner.invoke(
                self.main_function,
                [
                    "--report",
                    str(working_dir / "finalreport.txt"),
                    "--snpfile",
                    str(working_dir / "snplist_3cols.txt"),
                    "--src_coding",
                    "ab",
                    "--assembly",
                    "OAR3",
                    "--species",
                    "Sheep",
                    "--results_dir",
                    results_dir,
                    "--chip_name",
                    self.chip_name,
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            plink_path = results_dir / "finalreport_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 2)

    def test_import_from_illumina_no_snpfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = working_dir / "results"

            # copy test data files
            self.link_files(working_dir)

            result = self.runner.invoke(
                self.main_function,
                [
                    "--report",
                    str(working_dir / "finalreport.txt"),
                    "--src_coding",
                    "ab",
                    "--assembly",
                    "OAR3",
                    "--species",
                    "Sheep",
                    "--results_dir",
                    results_dir,
                    "--chip_name",
                    self.chip_name,
                ]
            )

            self.assertEqual(1, result.exit_code, msg=result.exception)
            self.assertIsInstance(result.exception, RuntimeError)

            plink_path = results_dir / "finalreport_updated"
            self.assertFalse(plink_path.exists())


if __name__ == '__main__':
    unittest.main()
