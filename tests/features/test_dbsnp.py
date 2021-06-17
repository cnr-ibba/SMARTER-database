#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 16:30:05 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import unittest
import pathlib

from functools import partial

from src.features.dbsnp import search_chip_snps, read_dbSNP

# set data dir
DATA_DIR = pathlib.Path(__file__).parent / "data"

search_agr_bs = partial(search_chip_snps, handle='AGR_BS')


class DBSNPTest(unittest.TestCase):
    def setUp(self):
        self.dbsnp_path = DATA_DIR / "ds_test.xml"
        self.iterator = filter(search_agr_bs, read_dbSNP(self.dbsnp_path))
        self.snp = next(self.iterator)

    def test_snp(self):
        self.assertEqual(self.snp['rsId'], "55627891")

    def test_ss(self):
        test = next(
            filter(
                lambda ss: ss['locSnpId'] == 'DU170943_581.1',
                self.snp['ss'])
            )

        reference = {
            'ssId': '836318739',
            'handle': 'AGR_BS',
            'batchId': '1059595',
            'locSnpId': 'DU170943_581.1',
            'subSnpClass': 'snp',
            'orient': 'forward',
            'strand': 'bottom',
            'molType': 'genomic',
            'buildId': '140',
            'methodClass': 'hybridize',
            'validated': 'by-submitter',
            'seq5': ('TCCAGTTTCAGATTTTGCCTTAGGCTCCTGAGTCAACAG'
                     'GAGAGGCGTCCCCTTCCAGCT'),
            'observed': 'G/T',
            'seq3': ('AACTGGCCTAGTCAGGTGCGGGGCATCCTAGACCATTCC'
                     'TGGTAGGGCTCTGCTGTCTTC')
        }

        self.assertDictEqual(reference, test)
