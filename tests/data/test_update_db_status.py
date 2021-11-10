#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 18:19:06 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import unittest

from click.testing import CliRunner

from src import __version__
from src.features.smarterdb import SmarterInfo
from src.data.common import WORKING_ASSEMBLIES, PLINK_SPECIES_OPT
from src.data.update_db_status import main as update_db_status

from ..common import MongoMockMixin


class UpdateDBStatusTest(MongoMockMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.working_assemblies = json.loads(json.dumps(WORKING_ASSEMBLIES))
        self.plink_specie_opt = json.loads(json.dumps(PLINK_SPECIES_OPT))

        self.runner = CliRunner()

    def test_help(self):
        result = self.runner.invoke(update_db_status, ["--help"])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Usage: main', result.output)

    def test_create_status(self):
        result = self.runner.invoke(update_db_status, [])

        self.assertEqual(0, result.exit_code)

        qs = SmarterInfo.objects()
        self.assertEqual(qs.count(), 1)

        info = qs.get()
        self.assertEqual(info.version, __version__)
        self.assertDictEqual(info.working_assemblies, self.working_assemblies)
        self.assertDictEqual(info.plink_specie_opt, self.plink_specie_opt)

    def test_update_status(self):
        # create an initial object
        info = SmarterInfo(id="smarter", version="old")
        info.save()

        result = self.runner.invoke(update_db_status, [])

        self.assertEqual(0, result.exit_code)

        qs = SmarterInfo.objects()
        self.assertEqual(qs.count(), 1)

        info = qs.get()
        self.assertEqual(info.version, __version__)
        self.assertDictEqual(info.working_assemblies, self.working_assemblies)
        self.assertDictEqual(info.plink_specie_opt, self.plink_specie_opt)
