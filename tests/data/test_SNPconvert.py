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

from ..common import (
    MongoMockMixin, VariantsMixin, SupportedChipMixin)

DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"


class SNPconvertTest(
        VariantsMixin, SupportedChipMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.mapfile = DATA_DIR / "plinktest.map"
        self.pedfile = DATA_DIR / "plinktest.ped"
        self.bedfile = DATA_DIR / "plinktest.bed"
        self.bimfile = DATA_DIR / "plinktest.bim"
        self.famfile = DATA_DIR / "plinktest.fam"
        self.snpfile = DATA_DIR / "snplist.txt"
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
        report = working_dir / "finalreport.txt"

        # create links
        mapfile.symlink_to(self.mapfile)
        pedfile.symlink_to(self.pedfile)
        bedfile.symlink_to(self.bedfile)
        bimfile.symlink_to(self.bimfile)
        famfile.symlink_to(self.famfile)
        snpfile.symlink_to(self.snpfile)
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
                    "--coding",
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


if __name__ == '__main__':
    unittest.main()
