#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 16:19:29 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import tempfile

from openpyxl import Workbook
from click.testing import CliRunner
from unittest.mock import patch, PropertyMock

from src.data.import_metadata import main as import_metadata
from src.features.smarterdb import Dataset, SampleSheep

from ..common import MongoMockMixin


class TestImportMetadata(MongoMockMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # need a dataset for certain tests
        cls.src_dataset = Dataset(
            file="test.zip",
            country="Italy",
            species="Sheep",
            contents=[
                "plinktest.map",
                "plinktest.ped",
                "metadata.xlsx"
            ]
        )
        cls.src_dataset.save()

        # create a workbook
        cls.workbook = Workbook()
        cls.sheet = cls.workbook.active

        # adding header
        cls.sheet.cell(row=1, column=1, value="Code")
        cls.sheet.cell(row=1, column=2, value="Name")
        cls.sheet.cell(row=1, column=3, value="Country")
        cls.sheet.cell(row=1, column=4, value="Lat")
        cls.sheet.cell(row=1, column=5, value="Lon")
        cls.sheet.cell(row=1, column=6, value="Col1")
        cls.sheet.cell(row=1, column=7, value="Col 2")

        # adding values
        cls.sheet.cell(row=2, column=1, value="TEX")
        cls.sheet.cell(row=2, column=2, value="Texel")
        cls.sheet.cell(row=2, column=3, value="Italy")
        cls.sheet.cell(row=2, column=4, value=45.46427)
        cls.sheet.cell(row=2, column=5, value=9.18951)
        cls.sheet.cell(row=2, column=6, value="Val1")
        cls.sheet.cell(row=2, column=7, value="Val2")

    @classmethod
    def tearDownClass(cls):
        Dataset.objects.delete()
        SampleSheep.objects.delete()

        super().tearDownClass()

    def setUp(self):
        self.runner = CliRunner()

        # need also a sample
        self.sample = SampleSheep(
            original_id="test-1",
            smarter_id="ITOA-TEX-000000001",
            country="Italy",
            species="Sheep",
            breed="Texel",
            breed_code="TEX",
            dataset=self.src_dataset,
            chip_name="IlluminaOvineSNP50",
        )
        self.sample.save()

    def tearDown(self):
        SampleSheep.objects.delete()

        super().tearDown()

    def test_help(self):
        result = self.runner.invoke(import_metadata, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_with_position(self, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            my_working_dir.return_value = working_dir

            # save worksheet in temporary folder
            self.workbook.save(f"{working_dir}/metadata.xlsx")

            result = self.runner.invoke(
                import_metadata,
                [
                    "--src_dataset",
                    "test.zip",
                    "--datafile",
                    "metadata.xlsx",
                    "--breed_column",
                    "Name",
                    "--latitude_column",
                    "Lat",
                    "--longitude_column",
                    "Lon"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            self.sample.reload()
            self.assertEqual(
                self.sample.location,
                {
                    'type': 'Point',
                    'coordinates': [9.18951, 45.46427]
                }
            )

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_with_metadata(self, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            my_working_dir.return_value = working_dir

            # save worksheet in temporary folder
            self.workbook.save(f"{working_dir}/metadata.xlsx")

            result = self.runner.invoke(
                import_metadata,
                [
                    "--src_dataset",
                    "test.zip",
                    "--datafile",
                    "metadata.xlsx",
                    "--breed_column",
                    "Name",
                    "--metadata_column",
                    "Col1",
                    "--metadata_column",
                    "Col 2"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            self.sample.reload()
            self.assertEqual(
                self.sample.metadata,
                {
                    'col1': 'Val1',
                    'col_2': 'Val2'
                }
            )


if __name__ == '__main__':
    unittest.main()
