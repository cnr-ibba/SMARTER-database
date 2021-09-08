#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 15:07:41 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import tempfile

from click.testing import CliRunner
from unittest.mock import patch, PropertyMock

from src.data.import_datasets import main as import_datasets
from src.features.smarterdb import Dataset

from ..common import MongoMockMixin

DATA_DIR = pathlib.Path(__file__).parent / "data"


class ImportDatasetsTest(MongoMockMixin, unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.input_file = DATA_DIR / "test-genotypes-bg.csv"

    def test_help(self):
        result = self.runner.invoke(import_datasets, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    def tearDown(self):
        Dataset.objects.delete()

        super().tearDown()

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    @patch('src.data.import_datasets.get_raw_dir')
    def test_import_datasets(self, my_raw_dir, my_working_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            # define outputfile
            output_path = pathlib.Path(tmpdirname)
            output_file = output_path / "test-genotypes-bg.json"

            working_dir = pathlib.Path(tmpdirname)
            raw_dir = DATA_DIR / "raw"

            # assign return value to mocked property
            my_raw_dir.return_value = raw_dir
            my_working_dir.return_value = working_dir

            result = self.runner.invoke(
                import_datasets,
                [
                    "--types",
                    "genotype",
                    "background",
                    str(self.input_file),
                    str(output_file),
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(Dataset.objects.count(), 1)

            # get a dataset
            dataset = Dataset.objects.first()

            # assert empty fields
            self.assertIsNone(dataset.uploader)
            self.assertIsNone(dataset.partner)

            # assert chip name imported
            self.assertEqual(dataset.chip_name, "IlluminaOvineSNP50")

    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    @patch('src.data.import_datasets.get_raw_dir')
    def test_import_datasets_update(self, my_raw_dir, my_working_dir):
        # create a dataset object and simulate update
        dataset = Dataset(
            file="test.zip",
            country="Italy",
            species="Sheep",
            contents=[
                "plinktest.map",
                "plinktest.ped",
                "plinktest.fam",
                "plinktest.bim",
                "plinktest.bed",
                "snplist.txt",
                "finalreport.txt",
                "affytest.map",
                "affytest.ped"
            ]
        )
        dataset.save()

        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            # define outputfile
            output_path = pathlib.Path(tmpdirname)
            output_file = output_path / "test-genotypes-bg.json"

            working_dir = pathlib.Path(tmpdirname)
            raw_dir = DATA_DIR / "raw"

            # assign return value to mocked property
            my_raw_dir.return_value = raw_dir
            my_working_dir.return_value = working_dir

            result = self.runner.invoke(
                import_datasets,
                [
                    "--types",
                    "genotype",
                    "background",
                    str(self.input_file),
                    str(output_file),
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(Dataset.objects.count(), 1)

            # get a dataset
            dataset = Dataset.objects.first()

            # assert empty fields
            self.assertIsNone(dataset.uploader)
            self.assertIsNone(dataset.partner)

            # assert chip name imported
            self.assertEqual(dataset.chip_name, "IlluminaOvineSNP50")


if __name__ == '__main__':
    unittest.main()
