#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  4 15:26:46 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest

from click.testing import CliRunner

from src.data.import_samples import main as import_samples


class TestImportSamples(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_help(self):
        result = self.runner.invoke(import_samples, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)


if __name__ == '__main__':
    unittest.main()
