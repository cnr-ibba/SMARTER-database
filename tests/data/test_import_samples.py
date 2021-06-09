#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  4 15:26:46 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import tempfile

from openpyxl import Workbook
from click.testing import CliRunner
from unittest.mock import patch, PropertyMock

from src.data.import_samples import main as import_samples
from src.features.smarterdb import Dataset, SampleSheep, SEX

from ..common import (
    MongoMockMixin, SmarterIDMixin, SupportedChipMixin)


class TestImportSamples(
        SmarterIDMixin, SupportedChipMixin, MongoMockMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # getting destination dataset
        cls.dst_dataset = Dataset.objects.get(file="test.zip")

        # create a src dataset
        cls.src_dataset = Dataset(
            file="test2.zip",
            country="Italy",
            species="Sheep",
            contents=[
                "metadata.xlsx"
            ]
        )
        cls.src_dataset.save()

        # create a workbook
        cls.workbook = Workbook()
        cls.sheet = cls.workbook.active

        # adding header
        cls.sheet.cell(row=1, column=1, value="Code")
        cls.sheet.cell(row=1, column=2, value="Id")
        cls.sheet.cell(row=1, column=3, value="Country")
        cls.sheet.cell(row=1, column=4, value="Sex")

        # adding values
        cls.sheet.cell(row=2, column=1, value="TEX_IT")
        cls.sheet.cell(row=2, column=2, value="test-1")
        cls.sheet.cell(row=2, column=3, value="Italy")
        cls.sheet.cell(row=2, column=4, value="BHO")

        # adding values
        cls.sheet.cell(row=3, column=1, value="TEX_IT")
        cls.sheet.cell(row=3, column=2, value="test-2")
        cls.sheet.cell(row=3, column=3, value="SPAIN")
        cls.sheet.cell(row=3, column=4, value="F")

    def setUp(self):
        self.runner = CliRunner()

        # add a sample in database
        self.sample = SampleSheep(
            original_id="test-1",
            country="Italy",
            species="Sheep",
            breed="Texel",
            breed_code="TEX",
            dataset=self.dst_dataset,
            chip_name=self.chip_name,
        )
        self.sample.save()

    def tearDown(self):
        SampleSheep.objects.delete()

        super().tearDown()

    def test_help(self):
        result = self.runner.invoke(import_samples, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_mandatory(self, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            my_working_dir.return_value = working_dir

            # save worksheet in temporary folder
            self.workbook.save(f"{working_dir}/metadata.xlsx")

            # got first sample from database
            self.assertEqual(SampleSheep.objects.count(), 1)

            result = self.runner.invoke(
                import_samples,
                [
                    "--src_dataset",
                    "test2.zip",
                    "--dst_dataset",
                    "test.zip",
                    "--datafile",
                    "metadata.xlsx",
                    "--code_column",
                    "Code",
                    "--country_column",
                    "Country",
                    "--id_column",
                    "Id",
                    "--chip_name",
                    self.chip_name
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            # I should have two record for samples, One already present one new
            self.assertEqual(SampleSheep.objects.count(), 2)

            # get the new sample
            sample = SampleSheep.objects.get(original_id="test-2")
            self.assertEqual(sample.smarter_id, "ESOA-TEX-000000002")

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_with_sex(self, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            my_working_dir.return_value = working_dir

            # save worksheet in temporary folder
            self.workbook.save(f"{working_dir}/metadata.xlsx")

            # got first sample from database
            self.assertEqual(SampleSheep.objects.count(), 1)

            result = self.runner.invoke(
                import_samples,
                [
                    "--src_dataset",
                    "test2.zip",
                    "--dst_dataset",
                    "test.zip",
                    "--datafile",
                    "metadata.xlsx",
                    "--code_column",
                    "Code",
                    "--country_column",
                    "Country",
                    "--id_column",
                    "Id",
                    "--sex_column",
                    "Sex",
                    "--chip_name",
                    self.chip_name
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            # I should have two record for samples, One already present one new
            self.assertEqual(SampleSheep.objects.count(), 2)

            # first sampla wasn't been updated. Unknown sex
            self.sample.reload()
            self.assertIsNone(self.sample.sex)

            # get the new sample
            sample = SampleSheep.objects.get(original_id="test-2")
            self.assertEqual(sample.smarter_id, "ESOA-TEX-000000002")
            self.assertEqual(sample.sex, SEX.FEMALE)


if __name__ == '__main__':
    unittest.main()
