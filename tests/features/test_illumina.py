#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  3 17:09:17 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import pathlib
import unittest
import types
import datetime
import collections

from io import StringIO

from src.features.illumina import (
    read_snpMap, read_Manifest, read_snpList, read_illuminaRow, skip_lines,
    skip_until_section, search_manifactured_date, IlluSNP, IlluSNPException)

FEATURE_DATA_DIR = pathlib.Path(__file__).parents[1] / "features/data"
SCRIPTS_DATA_DIR = pathlib.Path(__file__).parents[1] / "data/data"


class SkipTest(unittest.TestCase):
    data_path = SCRIPTS_DATA_DIR / "test_manifest.csv"

    def test_skip_lines(self):
        reference = [
            "Illumina, Inc.,,,,,,,,,,,,,,,,,,,",
            "[Heading],,,,,,,,,,,,,,,,,,,,",
            "Descriptor File Name,OvineSNP50_B.bpm,,,,,,,,,,,,,,,,,,,",
            "Assay Format,Infinium HD Ultra,,,,,,,,,,,,,,,,,,,",
            "Date Manufactured,1/7/2009,,,,,,,,,,,,,,,,,,,",
            "Loci Count ,54241,,,,,,,,,,,,,,,,,,,",
            "[Assay],,,,,,,,,,,,,,,,,,,,",
        ]
        with open(self.data_path) as handle:
            _, skipped = skip_lines(handle, skip=7)

        self.assertListEqual(skipped, reference)

    def test_skip_until_section(self):
        reference = [
            "Illumina, Inc.,,,,,,,,,,,,,,,,,,,",
            "[Heading],,,,,,,,,,,,,,,,,,,,",
            "Descriptor File Name,OvineSNP50_B.bpm,,,,,,,,,,,,,,,,,,,",
            "Assay Format,Infinium HD Ultra,,,,,,,,,,,,,,,,,,,",
            "Date Manufactured,1/7/2009,,,,,,,,,,,,,,,,,,,",
            "Loci Count ,54241,,,,,,,,,,,,,,,,,,,",
            "[Assay],,,,,,,,,,,,,,,,,,,,",
        ]
        with open(self.data_path) as handle:
            _, skipped = skip_until_section(handle, "[Assay]")

        self.assertListEqual(skipped, reference)

    def test_search_manifactured_date(self):
        with open(self.data_path) as handle:
            _, skipped = skip_until_section(handle, "[Assay]")

        test = search_manifactured_date(skipped)
        reference = datetime.datetime(2009, 1, 7)

        self.assertEqual(reference, test)


class IlluminaMixin():
    data_path = None
    snp_name = None
    delimiter = None
    skip_lines = 2

    def read_func(self, *args, **kwargs):
        raise NotImplementedError("Please set this in child classes")

    def common(self, iterator):
        self.assertIsInstance(iterator, types.GeneratorType)

        test = next(iterator)
        self.assertEqual(test.name, self.snp_name)

    def test_read(self):
        iterator = self.read_func(path=self.data_path)
        self.common(iterator)

    def test_read_skip(self):
        iterator = self.read_func(path=self.data_path, skip=self.skip_lines)
        self.common(iterator)

    def test_read_delimiter(self):
        iterator = self.read_func(
            path=self.data_path, delimiter=self.delimiter)
        self.common(iterator)


class ReadSNPMapTest(IlluminaMixin, unittest.TestCase):
    data_path = FEATURE_DATA_DIR / "illumina_snpmap.txt"
    snp_name = "250506CS3900065000002_1238.1"
    delimiter = "\t"

    def read_func(self, *args, **kwargs):
        return read_snpMap(*args, **kwargs)


class ReadManifest(IlluminaMixin, unittest.TestCase):
    data_path = SCRIPTS_DATA_DIR / "test_manifest.csv"
    snp_name = "250506CS3900065000002_1238.1"
    delimiter = ","
    skip_lines = 7

    def read_func(self, *args, **kwargs):
        return read_Manifest(*args, **kwargs, size=2026)


class ReadSnpListTest(IlluminaMixin, unittest.TestCase):
    data_path = FEATURE_DATA_DIR / "snplist.txt"
    snp_name = "250506CS3900140500001_312.1"
    delimiter = "\t"

    def read_func(self, *args, **kwargs):
        return read_snpList(*args, **kwargs)


class ReadSnpList3colsTest(IlluminaMixin, unittest.TestCase):
    """Test reading a SNPlist file with only 3 columns"""
    data_path = FEATURE_DATA_DIR / "snplist_3cols.txt"
    snp_name = "250506CS3900140500001_312.1"
    delimiter = "\t"

    def read_func(self, *args, **kwargs):
        return read_snpList(*args, **kwargs)


class ReadIlluminaRowTest(unittest.TestCase):
    data_path = FEATURE_DATA_DIR / "finalreport.txt"
    snp_name = "250506CS3900140500001_312.1"

    def test_read(self):
        iterator = self.read_func(path=self.data_path)
        self.assertIsInstance(iterator, types.GeneratorType)

        test = next(iterator)
        self.assertEqual(test.snp_name, self.snp_name)

    def read_func(self, *args, **kwargs):
        return read_illuminaRow(*args, **kwargs)


# define namedtuple objects
SNPrecord = collections.namedtuple("SNPrecord", "snp_name sequence strand A B")


# A function to read snps tables in namedtuple objects
def readSNPtable(table):
    handle = StringIO(table)
    reader = csv.reader(handle, delimiter=",", lineterminator="\n")
    return [SNPrecord._make(record) for record in reader]


class TestIlluCoding(unittest.TestCase):
    """Test for illumina conversion"""

    def setUp(self):
        # defining unambigous SNPs
        unambiguous_table = """rs363040,AGGAGGCTAG[G/T]CTCGCAGAGC,BOT,T,G
rs536477,GAGATTTAGG[A/G]AAAGATGTGA,TOP,A,G
rs684517,ACCAGGTACT[C/T]TGAACTTTAC,BOT,T,C
fake1,ACCAGGTACT[T/C]TGAACTTTAC,BOT,T,C
rs2034107,CATCTCCCCC[A/C]AAATCAGTTT,TOP,A,C"""

        self.unambiguous_table = readSNPtable(unambiguous_table)

        # defining ambiguous SNPs
        ambiguous_table = """rs1535632,ACGGGGACAG[A/T]TATGTTAACT,BOT,T,A
rs363334,ATGAGTGAAT[C/G]AAGCACTATT,TOP,C,G
rs7101540,AAATTCAGAT[A/T]CAGAATCTTT,TOP,A,T
rs7113791,GATGGACAGG[A/T]TGACCTCTAG,BOT,T,A
rs778833,GGTTAAATGT[C/G]AAGGTGAGCT,BOT,G,C
rs4933195,ATGCTAATAA[A/T]ACATTAAAGT,TOP,A,T
rs903997,ATGAGAAAGT[C/G]TGAGAGTGCA,TOP,C,G
rs1942968,CTACATGACT[C/G]TTTATGTTAC,BOT,G,C"""

        self.ambiguous_table = readSNPtable(ambiguous_table)

        # defining snp in different assemblies
        assembly_table = """SNP1_Assembly1,GGACCCGCAA[G/A]GAGGGCGCGG,TOP,A,G
SNP1_Assembly2,CCGCGCCCTC[C/T]TTGCGGGTCC,BOT,T,C
SNP2_Assembly1,GGTAGCCTGA[A/T]ACCCCCAAGA,TOP,A,T
SNP2_Assembly2,TCTTGGGGGT[A/T]TCAGGCTACC,BOT,T,A
"""
        self.assembly_table = readSNPtable(assembly_table)

    def test_unambiguous(self):
        """Testing unambigous SNPs"""

        # define a IlluSNP object
        illusnp = IlluSNP()

        for snp_record in self.unambiguous_table:
            illusnp.fromSequence(snp_record.sequence)
            for attr in ["strand", "A", "B"]:
                illu_attr = getattr(illusnp, attr)
                record_attr = getattr(snp_record, attr)
                self.assertEqual(illu_attr, record_attr,
                                 msg="Testing %s (%s:%s)" % (attr, illu_attr,
                                                             record_attr))

    def test_ambiguous(self):
        """Testing ambiguous SNPs"""

        # define a IlluSNP object
        illusnp = IlluSNP()

        for snp_record in self.ambiguous_table:
            illusnp.fromSequence(snp_record.sequence)
            for attr in ["strand", "A", "B"]:
                illu_attr = getattr(illusnp, attr)
                record_attr = getattr(snp_record, attr)
                self.assertEqual(illu_attr, record_attr,
                                 msg="Testing %s (%s:%s)" % (attr, illu_attr,
                                                             record_attr))

        # testing max_iter (step 3 is the discriminant)
        snp_record = self.ambiguous_table[1]
        self.assertRaisesRegex(
            IlluSNPException,
            "Can't find unambiguous pair in 2 steps",
            illusnp.fromSequence,
            snp_record.sequence,
            max_iter=2)

    def test_assembly(self):
        """Testing assemblies"""

        # define a IlluSNP object
        illusnp = IlluSNP()

        for snp_record in self.assembly_table:
            illusnp.fromSequence(snp_record.sequence)
            for attr in ["strand", "A", "B"]:
                illu_attr = getattr(illusnp, attr)
                record_attr = getattr(snp_record, attr)
                self.assertEqual(illu_attr, record_attr,
                                 msg="Testing %s (%s:%s)" % (attr, illu_attr,
                                                             record_attr))


class testIlluSNP(unittest.TestCase):
    """Test IlluSNP obj"""

    def setUp(self):
        self.illusnp = IlluSNP()

    def test_init(self):
        """Testing instantiation"""

        test = IlluSNP(sequence="AGGAGGCTAG[G/T]CTCGCAGAGC")

        # test str representation
        self.assertIsInstance(test.__repr__(), str)

    def test_equal(self):
        """Test __eq__ method"""

        t1 = IlluSNP(sequence="AGGAGGCTAG[G/T]CTCGCAGAGC")
        t2 = IlluSNP(sequence="AGGAGGCTAG[G/T]CTCGCAGAGC")

        self.assertEqual(t1, t2)

    def test_not_equal(self):
        """Test __ne__ method"""

        t1 = IlluSNP(sequence="AGGAGGCTAG[G/T]CTCGCAGAGC")
        t2 = IlluSNP(sequence="AGGAGGCTAG[A/G]CTCGCAGAGC")

        self.assertNotEqual(t1, t2)

    def test_findSNP(self):
        positive = "AGGAGGCTAG[G/T]CTCGCAGAGC"
        snp, position = self.illusnp.findSNP(positive)

        # find SNP and position in sequence (0-based)
        self.assertEqual(snp, "G/T")
        self.assertEqual(position, (10, 15))

        # asserting error
        negatives = ["AGGAGGCTAGGCTCGCAGAGC", "AGGAGGCTAGG/TCTCGCAGAGC"]

        for negative in negatives:
            self.assertRaisesRegex(
                IlluSNPException,
                "Can't find a SNP in",
                self.illusnp.findSNP,
                negative)

    def test_isUnambiguous(self):
        # defining unambigous SNPs
        unambiguous = ["A/C", "A/G", "T/C", "T/G", "C/A", "C/T", "G/A", "G/T"]
        ambiguous = ["A/T", "C/G", "A/A", "G/G", "T/T", "C/C", "T/A", "G/C"]

        # check allele length
        self.assertRaisesRegex(
            IlluSNPException,
            "Too many alleles in",
            self.illusnp.isUnambiguous,
            "A/G/T")

        for snp in unambiguous:
            self.assertTrue(self.illusnp.isUnambiguous(snp),
                            msg="Testing unambiguous %s" % (snp))

        for snp in ambiguous:
            self.assertFalse(self.illusnp.isUnambiguous(snp),
                             msg="Testing ambiguous %s" % (snp))

    def test_toTop(self):
        # Trasnlate a BOT snp in TOP
        illu_snp = IlluSNP(sequence="AGGAGGCTAG[T/G]CTCGCAGAGC")
        test = illu_snp.toTop()
        ref = IlluSNP(sequence="GCTCTGCGAG[A/C]CTAGCCTCCT")

        self.assertEqual(test, ref)

        # get ifself if already in bot
        illu_snp = IlluSNP(sequence="GCTCTGCGAG[A/C]CTAGCCTCCT")
        test = illu_snp.toTop()

        self.assertEqual(test, illu_snp)

    def test_toTop_flank_not_equal(self):
        """Test illumina SNP where flanking sequences are not equal in
        length"""

        # Trasnlate a BOT snp in TOP
        illu_snp = IlluSNP(
            "TCCTTTGTGGGTGGAGAGGCTGACCCATTTGCAAG[C/T]"
            "AGATTTCAGACCTCCGGGCCCTTTACCCCC")
        test = illu_snp.toTop()
        ref = IlluSNP(
            "GGGGGTAAAGGGCCCGGAGGTCTGAAATCT[A/G]"
            "CTTGCAAATGGGTCAGCCTCTCCACCCACAAAGGA")

        self.assertEqual(test, ref)


if __name__ == '__main__':
    unittest.main()
