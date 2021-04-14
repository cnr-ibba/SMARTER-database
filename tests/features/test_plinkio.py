#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 17:42:03 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import types
import unittest
import pathlib
import tempfile

from src.features.smarterdb import (
    VariantSheep, Location, Breed, Dataset, SampleSheep)
from src.features.plinkio import (
    TextPlinkIO, MapRecord, CodingException, IlluminaReportIO)

from .common import MongoMockMixin, SmarterIDMixin

# set data dir (like os.dirname(__file__)) + "fixtures"
FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"
DATA_DIR = pathlib.Path(__file__).parent / "data"


class VariantsMixin():
    @classmethod
    def setUpClass(cls):
        # initialize the mongomock instance
        super().setUpClass()

        # load database variants into mock database
        with open(FIXTURES_DIR / "variants.json") as handle:
            cls.data = json.load(handle)

        # I can't track data with from_json like mongoengine does. I need
        # to instantiate objects from dict (without unsupported keys)
        for item in cls.data:
            del(item['_id'])
            variant = VariantSheep(**item)
            variant.save()

    @classmethod
    def tearDownClass(cls):
        VariantSheep.objects.delete()

        super().tearDownClass()


class TextPlinkIOMap(VariantsMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        self.plinkio = TextPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Sheep")

    def test_read_mapfile(self):
        self.plinkio.read_mapfile()
        self.assertIsInstance(self.plinkio.mapdata, list)
        self.assertEqual(len(self.plinkio.mapdata), 4)
        for record in self.plinkio.mapdata:
            self.assertIsInstance(record, MapRecord)

    def test_fetch_coordinates(self):
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(version="Oar_v3.1")

        self.assertIsInstance(self.plinkio.locations, list)
        self.assertEqual(len(self.plinkio.locations), 4)

        self.assertIsInstance(self.plinkio.filtered, set)
        self.assertEqual(len(self.plinkio.filtered), 1)

        # assert filtered items
        self.assertIn(3, self.plinkio.filtered)

        for idx, record in enumerate(self.plinkio.locations):
            if idx in self.plinkio.filtered:
                self.assertIsNone(record)
            else:
                self.assertIsInstance(record, Location)

    def test_update_mapfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.map"
            self.plinkio.read_mapfile()
            self.plinkio.fetch_coordinates(version="Oar_v3.1")
            self.plinkio.update_mapfile(str(outfile))

            # now open outputfile and test stuff
            test = TextPlinkIO(
                mapfile=str(outfile),
                pedfile=str(DATA_DIR / "plinktest.ped"))
            test.read_mapfile()

            # one snp cannot be mapped
            self.assertEqual(len(test.mapdata), 3)

            for record in test.mapdata:
                variant = VariantSheep.objects(name=record.name).get()
                location = variant.get_location(version="Oar_v3.1")
                self.assertEqual(location.chrom, record.chrom)
                self.assertEqual(location.position, record.position)

        # directory and contents have been removed


class TextPlinkIOPed(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):

    def setUp(self):
        self.plinkio = TextPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Sheep")

        # read info from map
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(version="Oar_v3.1")

        # read first line of ped file
        self.lines = list(self.plinkio.read_pedfile())

    def test_read_pedfile(self):
        test = self.plinkio.read_pedfile()
        self.assertIsInstance(test, types.GeneratorType)

        # consume data and count rows
        test = list(test)
        self.assertEqual(len(test), 2)

    def test_process_genotypes_top(self):
        # first record is in top coordinates
        line = self.lines[0]
        test = self.plinkio._process_genotypes(line, 'top')

        # a genotype in forward coordinates isn't modified
        self.assertEqual(line, test)

        # searching forward coordinates throws exception
        self.assertRaisesRegex(
            CodingException,
            "Not illumina forward format",
            self.plinkio._process_genotypes,
            line,
            "forward"
        )

        # searching ab coordinates throws exception
        self.assertRaisesRegex(
            CodingException,
            "Not illumina ab format",
            self.plinkio._process_genotypes,
            line,
            "ab"
        )

    def test_process_genotypes_forward(self):
        # read a file in forward coordinates
        self.plinkio.pedfile = str(DATA_DIR / "plinktest_forward.ped")
        forward = next(self.plinkio.read_pedfile())

        # searching top coordinates throws exception
        self.assertRaisesRegex(
            CodingException,
            "Not illumina top format",
            self.plinkio._process_genotypes,
            forward,
            "top"
        )

        # searching ab coordinates throws exception
        self.assertRaisesRegex(
            CodingException,
            "Not illumina ab format",
            self.plinkio._process_genotypes,
            forward,
            "ab"
        )

        test = self.plinkio._process_genotypes(forward, 'forward')

        # a genotype in forward coordinates returns in top
        reference = self.lines[0]
        self.assertEqual(reference, test)

    def test_process_genotypes_ab(self):
        # read a file in forward coordinates
        self.plinkio.pedfile = str(DATA_DIR / "plinktest_ab.ped")
        ab = next(self.plinkio.read_pedfile())

        # searching top coordinates throws exception
        self.assertRaisesRegex(
            CodingException,
            "Not illumina top format",
            self.plinkio._process_genotypes,
            ab,
            "top"
        )

        # searching forward coordinates throws exception
        self.assertRaisesRegex(
            CodingException,
            "Not illumina forward format",
            self.plinkio._process_genotypes,
            ab,
            "forward"
        )

        test = self.plinkio._process_genotypes(ab, 'ab')

        # a genotype in forward coordinates returns in top
        reference = self.lines[0]
        self.assertEqual(reference, test)

    def test_get_or_create_sample(self):
        # get a sample line
        line = self.lines[0]

        # get a breed
        breed = Breed.objects(aliases__in=[line[0]]).get()

        # no individulas for such breeds
        self.assertEqual(breed.n_individuals, 0)
        self.assertEqual(SampleSheep.objects.count(), 0)

        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        # calling my function and collect sample
        reference = self.plinkio.get_or_create_sample(line, dataset, breed)
        self.assertIsInstance(reference, SampleSheep)

        # assert an element in database
        self.assertEqual(SampleSheep.objects.count(), 1)

        # check individuals updated
        breed.reload()
        self.assertEqual(breed.n_individuals, 1)

        # calling this function twice, returns the same individual
        test = self.plinkio.get_or_create_sample(line, dataset, breed)
        self.assertIsInstance(test, SampleSheep)

        # assert an element in database
        self.assertEqual(SampleSheep.objects.count(), 1)

        # check individuals updated
        breed.reload()
        self.assertEqual(breed.n_individuals, 1)

        self.assertEqual(reference, test)

    def test_process_pedline(self):
        # get a sample line
        line = self.lines[0]

        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        test = self.plinkio._process_pedline(line, dataset, 'top')

        # define reference
        reference = line.copy()
        reference[0], reference[1] = ['TEX', 'ITOA-TEX-000000001']

        # trow away the last snps (not found in database)
        del(reference[-2:])

        self.assertEqual(reference, test)

    def test_update_pedfile(self):
        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.ped"
            self.plinkio.update_pedfile(str(outfile), dataset, 'top')

            # now open outputfile and test stuff
            test = TextPlinkIO(
                mapfile=str(DATA_DIR / "plinktest.map"),
                pedfile=str(outfile))

            # assert two records written
            self.assertEqual(len(list(test.read_pedfile())), 2)

        # directory and contents have been removed


class IlluminaReportIOMap(VariantsMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        self.plinkio = IlluminaReportIO(
            snpfile=str(DATA_DIR / "snplist.txt"),
            report=str(DATA_DIR / "finalreport.txt"),
            species="Sheep")

        self.plinkio.read_snpfile()

    def test_read_snpfile(self):
        self.assertIsInstance(self.plinkio.mapdata, list)
        self.assertEqual(len(self.plinkio.mapdata), 2)
        for record in self.plinkio.mapdata:
            self.assertIsInstance(record, tuple)

    def test_fetch_coordinates(self):
        self.plinkio.fetch_coordinates(version="Oar_v3.1")

        self.assertIsInstance(self.plinkio.locations, list)
        self.assertEqual(len(self.plinkio.locations), 2)

        self.assertIsInstance(self.plinkio.filtered, set)
        self.assertEqual(len(self.plinkio.filtered), 0)

        for idx, record in enumerate(self.plinkio.locations):
            self.assertIsInstance(record, Location)

    def test_update_mapfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            # this is the temporary output file
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.map"

            self.plinkio.fetch_coordinates(version="Oar_v3.1")
            self.plinkio.update_mapfile(str(outfile))

            # now open outputfile and test stuff
            test = TextPlinkIO(mapfile=str(outfile))
            test.read_mapfile()

            # there was only two snps into dataset
            # HINT: could be in final report SNPs not included in database?
            self.assertEqual(len(test.mapdata), 2)

            for record in test.mapdata:
                variant = VariantSheep.objects(name=record.name).get()
                location = variant.get_location(version="Oar_v3.1")
                self.assertEqual(location.chrom, record.chrom)
                self.assertEqual(location.position, record.position)

        # directory and contents have been removed


class IlluminaReportIOPed(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):

    def setUp(self):
        self.plinkio = IlluminaReportIO(
            snpfile=str(DATA_DIR / "snplist.txt"),
            report=str(DATA_DIR / "finalreport.txt"),
            species="Sheep")

        # read info from map
        self.plinkio.read_snpfile()
        self.plinkio.fetch_coordinates(version="Oar_v3.1")

    def test_read_reportfile(self):
        test = self.plinkio.read_reportfile()
        self.assertIsInstance(test, types.GeneratorType)

        # consume data and count rows
        test = list(test)
        self.assertEqual(len(test), 2)


if __name__ == '__main__':
    unittest.main()
