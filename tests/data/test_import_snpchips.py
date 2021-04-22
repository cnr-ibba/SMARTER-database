#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 12:22:12 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib

from click.testing import CliRunner

from src.data.import_snpchips import main as import_snpchips
from src.features.smarterdb import IlluminaChip

from ..features.common import MongoMockMixin

DATA_DIR = pathlib.Path(__file__).parent / "data"


class ImportSNPChipsTest(MongoMockMixin, unittest.TestCase):
    main_function = import_snpchips

    def setUp(self):
        super().setUp()

        self.runner = CliRunner()

    def tearDown(self):
        IlluminaChip.objects.delete()

        super().tearDown()

    # HINT: move to a common Mixin?
    def test_help(self):
        result = self.runner.invoke(self.main_function, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    def test_import_snpchips(self):
        chip_file = DATA_DIR / "test_chip_names.json"

        result = self.runner.invoke(
            self.main_function,
            [
                "--chip_file",
                str(chip_file)
            ]
        )

        self.assertEqual(0, result.exit_code)

        qs = IlluminaChip.objects()
        self.assertEqual(qs.count(), 1)
