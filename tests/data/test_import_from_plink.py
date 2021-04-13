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
from src.features.smarterdb import SampleSheep

from ..features.common import MongoMockMixin, SmarterIDMixin
from ..features.test_plinkio import VariantsMixin

DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"


class TestImportFromPlink(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        # need to delete object from db after import
        SampleSheep.objects.delete()

        super().tearDownClass()

    def setUp(self):
        self.runner = CliRunner()
        self.mapfile = DATA_DIR / "plinktest.map"
        self.pedfile = DATA_DIR / "plinktest.ped"

    def link_files(self, working_dir):
        mapfile = working_dir / "plinktest.map"
        pedfile = working_dir / "plinktest.ped"

        mapfile.symlink_to(self.mapfile)
        pedfile.symlink_to(self.pedfile)

    def test_help(self):
        result = self.runner.invoke(import_from_plink, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    @patch('src.features.smarterdb.Dataset.result_dir',
           new_callable=PropertyMock)
    @patch('src.features.smarterdb.Dataset.working_dir',
           new_callable=PropertyMock)
    def test_import_from_plink(self, my_working_dir, my_result_dir):
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
                    "--mapfile",
                    "plinktest.map",
                    "--pedfile",
                    "plinktest.ped"
                ]
            )

            self.assertEqual(0, result.exit_code)
            self.assertEqual(SampleSheep.objects.count(), 2)

            plink_path = results_dir / "OARV3" / "plinktest_updated"
            plink_file = plinkfile.open(str(plink_path))

            sample_list = plink_file.get_samples()
            locus_list = plink_file.get_loci()

            self.assertEqual(len(sample_list), 2)
            self.assertEqual(len(locus_list), 3)


if __name__ == '__main__':
    unittest.main()
