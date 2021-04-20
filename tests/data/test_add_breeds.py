#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 14:56:16 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import tempfile

import pandas as pd
from openpyxl import Workbook
from click.testing import CliRunner
from unittest.mock import patch, PropertyMock

from src.features.smarterdb import Breed, Dataset
from src.data.add_breed import main as add_breed
from src.data.import_breeds import main as import_breeds

from ..features.common import MongoMockMixin


class BreedMixin():
    main_function = None

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()

    def tearDown(self):
        # drop all created breed
        Breed.objects.delete()

        super().tearDown()

    def test_help(self):
        result = self.runner.invoke(self.main_function, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)


class AddBreedTest(BreedMixin, MongoMockMixin, unittest.TestCase):
    main_function = add_breed

    def test_add_breed(self):
        result = self.runner.invoke(
            self.main_function,
            [
                "--species",
                "sheep",
                "--name",
                "Texel",
                "--code",
                "TEX",
                "--alias",
                "TEXEL_IT",
                "--alias",
                "0"
            ]
        )

        self.assertEqual(0, result.exit_code)

        qs = Breed.objects()
        self.assertEqual(qs.count(), 1)

        breed = qs.get()
        self.assertEqual(breed.aliases, ["TEXEL_IT", "0"])


class ImportBreedsTest(BreedMixin, MongoMockMixin, unittest.TestCase):
    main_function = import_breeds

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # need a dataset for certain tests
        cls.dataset = Dataset(
            file="test.zip",
            country="Italy",
            species="Sheep",
            contents=[
                "plinktest.map",
                "plinktest.ped",
                "breed.xlsx"
            ]
        )
        cls.dataset.save()

        # create a workbook
        cls.workbook = Workbook()
        cls.sheet = cls.workbook.active

        # adding header
        cls.sheet.cell(row=1, column=1, value="Code")
        cls.sheet.cell(row=1, column=2, value="Name")

        # adding values
        cls.sheet.cell(row=2, column=1, value="TEX")
        cls.sheet.cell(row=2, column=2, value="Texel")

    @classmethod
    def tearDownClass(cls):
        Dataset.objects.delete()

        super().tearDownClass()

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_breeds(self, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            my_working_dir.return_value = working_dir

            # save worksheet in temporary folder
            self.workbook.save(f"{working_dir}/breed.xlsx")

            result = self.runner.invoke(
                self.main_function,
                [
                    "--species",
                    "sheep",
                    "--dataset",
                    "test.zip",
                    "--datafile",
                    "breed.xlsx",
                    "--code_column",
                    "Code",
                    "--breed_column",
                    "Name"
                ]
            )

            self.assertEqual(0, result.exit_code)

            qs = Breed.objects()
            self.assertEqual(qs.count(), 1)

            breed = qs.get()
            self.assertEqual(breed.aliases, [])


if __name__ == '__main__':
    unittest.main()
