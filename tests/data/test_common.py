#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 15:45:36 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import pathlib
import unittest
import tempfile

from unittest.mock import patch, PropertyMock

from src.data.common import fetch_and_check_dataset, get_variant_species
from src.features.smarterdb import Dataset, VariantGoat, VariantSheep

from ..common import MongoMockMixin, SmarterIDMixin

DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"


class CommonScriptTest(SmarterIDMixin, MongoMockMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snpfile = DATA_DIR / "snplist.txt"
        cls.report = DATA_DIR / "finalreport.txt"
        cls.archive = "test.zip"
        cls.contents = ["snplist.txt", "finalreport.txt"]

        super().setUpClass()

    def link_files(self, working_dir):
        snpfile = working_dir / "snplist.txt"
        report = working_dir / "finalreport.txt"

        snpfile.symlink_to(self.snpfile)
        report.symlink_to(self.report)

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_get_dataset_with_stuff(self, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)

            # assign return value to mocked property
            my_working_dir.return_value = working_dir

            # copy test data files
            self.link_files(working_dir)

            # test stuff
            dataset, [snplist, finalreport] = fetch_and_check_dataset(
                archive=self.archive,
                contents=self.contents,
            )

            self.assertIsInstance(dataset, Dataset)
            self.assertIsInstance(snplist, pathlib.Path)
            self.assertIsInstance(finalreport, pathlib.Path)

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_file_not_in_dataset(self, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)

            # assign return value to mocked property
            my_working_dir.return_value = working_dir

            # copy test data files
            self.link_files(working_dir)

            # test stuff
            self.assertRaisesRegex(
                FileNotFoundError,
                r"Couldn't find '\['not_present.txt'\]'",
                fetch_and_check_dataset,
                self.archive,
                ["not_present.txt"]
            )

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_file_not_in_workdir(self, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)

            # assign return value to mocked property
            my_working_dir.return_value = working_dir

            # don't create test file symlinks in directory

            self.assertRaisesRegex(
                FileNotFoundError,
                r"Couldn't find '\['snplist.txt', 'finalreport.txt'\]'",
                fetch_and_check_dataset,
                self.archive,
                self.contents
            )

    def test_workingdir_not_exists(self):
        # don't create a wroking dir
        self.assertRaisesRegex(
            FileNotFoundError,
            "Could find dataset directory",
            fetch_and_check_dataset,
            self.archive,
            self.contents
        )


class GetVariantSpeciesTest(unittest.TestCase):
    def test_get_variant_sheep(self):
        VariantSpecies = get_variant_species(species="Sheep")
        self.assertEqual(VariantSpecies, VariantSheep)

    def test_get_variant_goat(self):
        VariantSpecies = get_variant_species(species="Goat")
        self.assertEqual(VariantSpecies, VariantGoat)

    def test_unmanaged_species(self):
        self.assertRaisesRegex(
            NotImplementedError,
            "not yet implemented",
            get_variant_species,
            "unmanaged"
        )


if __name__ == '__main__':
    unittest.main()
