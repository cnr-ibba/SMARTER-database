#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 17:42:03 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import types
import unittest
import pathlib
import tempfile
from copy import deepcopy

from src.features.smarterdb import (
    VariantSheep, Location, Breed, Dataset, SampleSheep, SEX)
from src.features.plinkio import (
    TextPlinkIO, MapRecord, CodingException, IlluminaReportIO, BinaryPlinkIO)

from ..common import MongoMockMixin, SmarterIDMixin, VariantsMixin

# set data dir
DATA_DIR = pathlib.Path(__file__).parent / "data"


class TextPlinkIOMap(VariantsMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

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
        self.plinkio.fetch_coordinates(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

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
            self.plinkio.fetch_coordinates(
                version="Oar_v3.1", imported_from="SNPchiMp v.3")
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
                location = variant.get_location(
                    version="Oar_v3.1", imported_from="SNPchiMp v.3")
                self.assertEqual(location.chrom, record.chrom)
                self.assertEqual(location.position, record.position)


class TextPlinkIOPed(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.plinkio = TextPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Sheep")

        # read info from map
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

        # read first line of ped file
        self.lines = list(self.plinkio.read_pedfile())

        # get a dataset
        self.dataset = Dataset.objects(file="test.zip").get()

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
        breed = Breed.objects(
            aliases__match={'fid': line[0], 'dataset': self.dataset}).get()

        # no individulas for such breeds
        self.assertEqual(breed.n_individuals, 0)
        self.assertEqual(SampleSheep.objects.count(), 0)

        # calling my function and collect sample
        reference = self.plinkio.get_or_create_sample(
            line, self.dataset, breed)
        self.assertIsInstance(reference, SampleSheep)

        # assert an element in database
        self.assertEqual(SampleSheep.objects.count(), 1)

        # check individuals updated
        breed.reload()
        self.assertEqual(breed.n_individuals, 1)

        # calling this function twice, returns the same individual
        test = self.plinkio.get_or_create_sample(line, self.dataset, breed)
        self.assertIsInstance(test, SampleSheep)

        # assert an element in database
        self.assertEqual(SampleSheep.objects.count(), 1)

        # check individuals updated
        breed.reload()
        self.assertEqual(breed.n_individuals, 1)

        self.assertEqual(reference, test)

    def test_sample_relies_dataset(self):
        """Getting two sample with the same original id is not a problem"""

        # get a sample line
        line = self.lines[0]

        # get a breed
        breed = Breed.objects(
            aliases__match={'fid': line[0], 'dataset': self.dataset}).get()

        # create a copy of dataset
        new_dataset = deepcopy(self.dataset)

        new_dataset.file = "test2.zip"
        new_dataset.id = None
        new_dataset.save()

        # ok create a samplesheep object with the same original_id
        first = self.plinkio.get_or_create_sample(line, self.dataset, breed)
        second = self.plinkio.get_or_create_sample(line, new_dataset, breed)

        self.assertEqual(SampleSheep.objects.count(), 2)
        self.assertEqual(first.original_id, second.original_id)

        # need to delete second sample in order to remove the new dataset
        # (mongoengine.DENY behaviour for deleting samples)
        second.delete()
        first.delete()

        # reset database to original state
        new_dataset.delete()

    def test_process_pedline(self):
        # get a sample line
        line = self.lines[0]

        test = self.plinkio._process_pedline(line, self.dataset, 'top')

        # define reference
        reference = line.copy()
        reference[0], reference[1] = ['TEX', 'ITOA-TEX-000000001']

        # trow away the last snps (not found in database)
        del(reference[-2:])

        self.assertEqual(reference, test)

    def get_relationships(self):
        """Helper function to define fake relationships"""

        # get a sample line
        line = self.lines[0]

        # make a copy and change some values
        father = deepcopy(line)
        mother = deepcopy(line)
        child = deepcopy(line)

        # let's start with father. Change id and sex column
        father[1], father[4] = "1", "1"

        # now the mother (same columns)
        mother[1], mother[4] = "2", "2"

        # the last is child. set id and and other records (unknown sex)
        child[1], child[2], child[3] = "3", "1", "2"

        return father, mother, child

    def test_process_pedline_relationship(self):
        """Test a pedline with father or mother ids"""

        father, mother, child = self.get_relationships()

        # process data and insert records
        for i, item in enumerate([father, mother, child]):
            test = self.plinkio._process_pedline(item, self.dataset, 'top')

            # define smarter_id
            smarter_id = f"ITOA-TEX-00000000{i+1}"

            # test ped line items
            self.assertEqual(test[0], "TEX")
            self.assertEqual(test[1], smarter_id)
            self.assertEqual(test[4], item[4])

            # assert database objects
            sample = SampleSheep.objects(smarter_id=smarter_id).get()

            # special child case
            if item == child:
                sample_father = SampleSheep.objects(
                    original_id=item[2],
                    dataset=self.dataset).get()
                sample_mother = SampleSheep.objects(
                    original_id=item[3],
                    dataset=self.dataset).get()

                self.assertIsNone(sample.sex)
                self.assertEqual(sample.father_id, sample_father)
                self.assertEqual(sample.mother_id, sample_mother)
                self.assertEqual(test[2], sample_father.smarter_id)
                self.assertEqual(test[3], sample_mother.smarter_id)

            else:
                self.assertEqual(sample.sex, SEX(int(item[4])))

    def test_update_relationship(self):
        """Test the possibility to update a sample relationship"""

        # ped lines could be in the wrong order. In such way, a child sample
        # could be written before its parents, and so ped lines can't be
        # written correctly

        # define fake relationships
        father, mother, child = self.get_relationships()

        # process data and insert records
        for i, item in enumerate([child, father, mother]):
            self.plinkio._process_pedline(item, self.dataset, 'top')

            # special child case
            if item == child:
                # define smarter_id
                smarter_id = f"ITOA-TEX-00000000{i+1}"

                # assert database objects
                sample_child = SampleSheep.objects(smarter_id=smarter_id).get()

        # assert child has no relationship
        self.assertIsNone(sample_child.father_id)
        self.assertIsNone(sample_child.mother_id)
        self.assertIsNone(sample_child.sex)

        # ok now try to process child again
        test = self.plinkio._process_pedline(child, self.dataset, 'top')

        # refresh database object
        sample_child.reload()
        sample_father = sample_child.father_id.fetch()
        sample_mother = sample_child.mother_id.fetch()

        self.assertEqual(sample_child.smarter_id, test[1])
        self.assertEqual(sample_father.smarter_id, test[2])
        self.assertEqual(sample_mother.smarter_id, test[3])

    def test_unmanaged_relationship(self):
        "test unsetting ped columns if relationship can be derived from data"

        # define fake relationships
        child = self.get_relationships()[-1]

        # insert child without parents
        test = self.plinkio._process_pedline(child, self.dataset, 'top')

        # define smarter_id
        smarter_id = f"ITOA-TEX-000000001"

        self.assertEqual(test[1], smarter_id)
        self.assertEqual(test[2], "0")
        self.assertEqual(test[3], "0")

    def test_update_pedfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.ped"
            self.plinkio.update_pedfile(str(outfile), self.dataset, 'top')

            # now open outputfile and test stuff
            test = TextPlinkIO(
                mapfile=str(DATA_DIR / "plinktest.map"),
                pedfile=str(outfile))

            # assert two records written
            self.assertEqual(len(list(test.read_pedfile())), 2)


class BinaryPlinkIOTest(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.plinkio = BinaryPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Sheep")

        # read info from map
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

        # read first line of ped file
        self.lines = list(self.plinkio.read_pedfile())

    def test_read_mapfile(self):
        self.assertIsInstance(self.plinkio.mapdata, list)
        self.assertEqual(len(self.plinkio.mapdata), 4)
        for record in self.plinkio.mapdata:
            self.assertIsInstance(record, MapRecord)

    def test_read_pedfile(self):
        test = self.plinkio.read_pedfile()
        self.assertIsInstance(test, types.GeneratorType)

        # consume data and count rows
        test = list(test)
        self.assertEqual(len(test), 2)

    def test_process_pedline(self):
        # define reference
        reference = [
            'TEX', 'ITOA-TEX-000000001', '0', '0', '0', -9,
            'A', 'A', 'A', 'G', 'G', 'G']

        # get a line for testing
        line = self.lines[0]

        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        test = self.plinkio._process_pedline(line, dataset, 'top')

        self.assertEqual(reference, test)


class IlluminaReportIOMap(VariantsMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

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
        self.plinkio.fetch_coordinates(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

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

            self.plinkio.fetch_coordinates(
                version="Oar_v3.1", imported_from="SNPchiMp v.3")
            self.plinkio.update_mapfile(str(outfile))

            # now open outputfile and test stuff
            test = TextPlinkIO(mapfile=str(outfile))
            test.read_mapfile()

            # there was only two snps into dataset
            # HINT: could be in final report SNPs not included in database?
            self.assertEqual(len(test.mapdata), 2)

            for record in test.mapdata:
                variant = VariantSheep.objects(name=record.name).get()
                location = variant.get_location(
                    version="Oar_v3.1", imported_from="SNPchiMp v.3")
                self.assertEqual(location.chrom, record.chrom)
                self.assertEqual(location.position, record.position)


class IlluminaReportIOPed(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.plinkio = IlluminaReportIO(
            snpfile=str(DATA_DIR / "snplist.txt"),
            report=str(DATA_DIR / "finalreport.txt"),
            species="Sheep")

        # read info from map
        self.plinkio.read_snpfile()
        self.plinkio.fetch_coordinates(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

        # read first line of ped file
        self.lines = list(self.plinkio.read_reportfile(fid="TEX"))

    def test_read_reportfile(self):
        test = self.plinkio.read_reportfile(fid="TEX")
        self.assertIsInstance(test, types.GeneratorType)

        # consume data and count rows
        test = list(test)
        self.assertEqual(len(test), 2)

    def test_process_pedline(self):
        # define reference
        reference = [
            'TEX', 'ITOA-TEX-000000001', '0', '0', '0', -9,
            'A', 'A', 'G', 'G']

        # get a line for testing
        line = self.lines[0]

        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        test = self.plinkio._process_pedline(line, dataset, 'ab')

        self.assertEqual(reference, test)

    def test_update_pedfile(self):
        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.ped"
            self.plinkio.update_pedfile(
                str(outfile), dataset, 'ab', fid="TEX")

            # now open outputfile and test stuff
            test = TextPlinkIO(
                mapfile=str(DATA_DIR / "plinktest.map"),
                pedfile=str(outfile))

            # assert two records written
            self.assertEqual(len(list(test.read_pedfile())), 2)


if __name__ == '__main__':
    unittest.main()
