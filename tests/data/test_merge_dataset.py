#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 10:44:45 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib
import tempfile

from click.testing import CliRunner
from unittest.mock import patch, PropertyMock
from plinkio import plinkfile

from src import __version__
from src.features.smarterdb import SampleSheep
from src.data.merge_datasets import main as merge_datasets

from ..common import MongoMockMixin, SmarterIDMixin, VariantsMixin

DATA_DIR = pathlib.Path(__file__).parent / "data"


class TestMergeDataset(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        # need to delete object from db after import
        SampleSheep.objects.delete()

        super().tearDownClass()

    def setUp(self):
        self.runner = CliRunner()

    def test_help(self):
        result = self.runner.invoke(merge_datasets, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    @patch('src.data.merge_datasets.get_processed_dir')
    @patch('src.data.merge_datasets.get_interim_dir')
    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    def test_merge(
            self, my_result_dir, my_interim_dir, my_processed_dir):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            working_dir = pathlib.Path(tmpdirname)
            results_dir = DATA_DIR / "processed"

            # assign return value to mocked property
            my_result_dir.return_value = results_dir
            my_interim_dir.return_value = working_dir
            my_processed_dir.return_value = working_dir

            result = self.runner.invoke(
                merge_datasets,
                [
                    "--species",
                    "sheep",
                    "--assembly",
                    "OAR3"
                ]
            )

            self.assertEqual(0, result.exit_code, msg=result.exception)

            smarter_tag = f"SMARTER-OA-OAR3-top-{__version__}"
            plink_path = working_dir / "OAR3" / smarter_tag
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)


if __name__ == '__main__':
    unittest.main()
