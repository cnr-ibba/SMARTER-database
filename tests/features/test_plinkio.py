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
    VariantSheep, Location, Breed, Dataset, SampleSheep, SEX, SampleGoat,
    VariantGoat)
from src.features.plinkio import (
    TextPlinkIO, MapRecord, CodingException, IlluminaReportIO, BinaryPlinkIO,
    AffyPlinkIO, AssemblyConf, AffyReportIO)

from ..common import (
    MongoMockMixin, SmarterIDMixin, VariantsMixin, SupportedChipMixin)

# set data dir
DATA_DIR = pathlib.Path(__file__).parent / "data"


class TextPlinkIOMap(VariantsMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.plinkio = TextPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Sheep")

        self.src_assembly = AssemblyConf(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

    def test_sheep_species(self):
        self.assertEqual(self.plinkio.VariantSpecies, VariantSheep)
        self.assertEqual(self.plinkio.SampleSpecies, SampleSheep)

    def test_goat_species(self):
        plinkio = TextPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Goat")

        self.assertEqual(plinkio.VariantSpecies, VariantGoat)
        self.assertEqual(plinkio.SampleSpecies, SampleGoat)

    def test_species_not_implemented(self):
        self.assertRaises(
            NotImplementedError,
            TextPlinkIO,
            prefix=str(DATA_DIR / "plinktest"),
            species="Foo")

    def test_read_mapfile(self):
        self.plinkio.read_mapfile()
        self.assertIsInstance(self.plinkio.mapdata, list)
        self.assertEqual(len(self.plinkio.mapdata), 4)
        for record in self.plinkio.mapdata:
            self.assertIsInstance(record, MapRecord)

    def test_fetch_coordinates(self):
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(
            src_assembly=self.src_assembly)

        self.assertIsInstance(self.plinkio.src_locations, list)
        self.assertEqual(len(self.plinkio.src_locations), 4)
        self.assertIsInstance(self.plinkio.dst_locations, list)
        self.assertEqual(len(self.plinkio.dst_locations), 4)

        self.assertIsInstance(self.plinkio.filtered, set)
        self.assertEqual(len(self.plinkio.filtered), 1)

        # assert filtered items
        self.assertIn(3, self.plinkio.filtered)

        for idx, record in enumerate(self.plinkio.dst_locations):
            if idx in self.plinkio.filtered:
                self.assertIsNone(record)
            else:
                self.assertIsInstance(record, Location)

    def test_update_mapfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.map"
            self.plinkio.read_mapfile()
            self.plinkio.fetch_coordinates(src_assembly=self.src_assembly)
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


class TextPlinkIOMapRSID(VariantsMixin, MongoMockMixin, unittest.TestCase):
    """A class to test plink files with rsid as SNP names"""

    def setUp(self):
        super().setUp()

        self.plinkio = TextPlinkIO(
            mapfile=str(DATA_DIR / "plinktest_rsid.map"),
            pedfile=str(DATA_DIR / "plinktest.ped"),
            species="Sheep")

        self.src_assembly = AssemblyConf(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

    def test_fetch_coordinates_by_rs_id(self):
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(
            src_assembly=self.src_assembly,
            search_field='rs_id'
        )

        self.assertIsInstance(self.plinkio.dst_locations, list)
        self.assertEqual(len(self.plinkio.dst_locations), 4)

        self.assertIsInstance(self.plinkio.filtered, set)
        self.assertEqual(len(self.plinkio.filtered), 2)

        # assert filtered items
        self.assertIn(0, self.plinkio.filtered)
        self.assertIn(3, self.plinkio.filtered)

        for idx, record in enumerate(self.plinkio.dst_locations):
            if idx in self.plinkio.filtered:
                self.assertIsNone(record)
            else:
                self.assertIsInstance(record, Location)


class TextPlinkIOPed(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.plinkio = TextPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Sheep")

        self.src_assembly = AssemblyConf(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

        # read info from map
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(src_assembly=self.src_assembly)

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

    def test_process_genotypes_half_missing(self):
        # read a file in forward coordinates
        self.plinkio.pedfile = str(DATA_DIR / "plinktest_half-missing.ped")
        half_missing = next(self.plinkio.read_pedfile())

        # processing top genotype
        test = self.plinkio._process_genotypes(half_missing, 'top')

        # an half-missing genotype should be set as MISSING
        reference = [
            'TEX_IT', '1', '0', '0', '0', '-9',
            '0', '0', 'A', 'G', '0', '0', '0', '0']

        self.assertEqual(reference, test)

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

    def test_get_sample(self):
        """get a sample without creating item"""

        # get a sample line
        line = self.lines[0]

        # get a breed
        breed = Breed.objects(
            aliases__match={'fid': line[0], 'dataset': self.dataset}).get()

        # no individulas for such breeds
        self.assertEqual(breed.n_individuals, 0)
        self.assertEqual(SampleSheep.objects.count(), 0)

        # calling my function and collect sample
        reference = self.plinkio.get_sample(
            line, self.dataset)

        # there are no sample in database, so get_sample returns none
        self.assertIsNone(reference)

        # assert no element in database
        self.assertEqual(SampleSheep.objects.count(), 0)

        # check individuals updated
        breed.reload()
        self.assertEqual(breed.n_individuals, 0)

        # call get_or_create to insert this sample in database
        test = self.plinkio.get_or_create_sample(line, self.dataset, breed)
        self.assertIsInstance(test, SampleSheep)

        # assert an element in database
        self.assertEqual(SampleSheep.objects.count(), 1)

        # check individuals updated
        breed.reload()
        self.assertEqual(breed.n_individuals, 1)

        # calling get_sample again to collect the sample
        reference = self.plinkio.get_sample(
            line,
            self.dataset
        )

        # now reference is a sample.
        self.assertIsInstance(reference, SampleSheep)

        # Check how many samples I have
        breed.reload()
        self.assertEqual(breed.n_individuals, 1)
        self.assertEqual(SampleSheep.objects.count(), 1)

        # check that objects are the same
        self.assertEqual(reference, test)

    def test_get_sample_breed_check(self):
        """get a sample without creating item"""

        # get a sample line
        line = self.lines[0]

        breed1 = Breed.objects(
            aliases__match={'fid': line[0], 'dataset': self.dataset}).get()

        # create a sample
        sample1 = self.plinkio.get_or_create_sample(line, self.dataset, breed1)

        # change the line and create a new sample
        line2 = line.copy()
        line2[0] = "MER_IT"

        breed2 = Breed.objects(
            aliases__match={'fid': line2[0], 'dataset': self.dataset}).get()

        # create another sample
        sample2 = self.plinkio.get_or_create_sample(
            line2, self.dataset, breed2)

        # ensure 2 samples created
        self.assertEqual(SampleSheep.objects.count(), 2)

        # calling get_sample to collect first sample
        test = self.plinkio.get_sample(
            line,
            self.dataset
        )

        self.assertIsInstance(test, SampleSheep)
        self.assertEqual(test, sample1)

        # calling get_sample to collect second sample
        test = self.plinkio.get_sample(
            line2,
            self.dataset
        )

        self.assertIsInstance(test, SampleSheep)
        self.assertEqual(test, sample2)

    def test_get_sample_by_alias(self):
        """get a sample without creating item"""

        # get a sample line
        line = self.lines[0].copy()

        # get a breed
        breed = Breed.objects(
            aliases__match={'fid': line[0], 'dataset': self.dataset}).get()

        # call get_or_create to insert this sample in database
        test = self.plinkio.get_or_create_sample(line, self.dataset, breed)

        # add an alias to this sample
        test.alias = "alias-1"
        test.save()

        # replace sample name with alias
        line[1] = "alias-1"

        # calling get_sample again to collect the sample
        reference = self.plinkio.get_sample(
            line,
            self.dataset,
            sample_field='alias'
        )

        # now reference is a sample.
        self.assertIsInstance(reference, SampleSheep)

        # Check how many samples I have
        breed.reload()
        self.assertEqual(breed.n_individuals, 1)
        self.assertEqual(SampleSheep.objects.count(), 1)

        # check that objects are the same
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

        test = self.plinkio._process_pedline(line, self.dataset, 'top', True)

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
            test = self.plinkio._process_pedline(
                item, self.dataset, 'top', True)

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
            self.plinkio._process_pedline(item, self.dataset, 'top', True)

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
        test = self.plinkio._process_pedline(child, self.dataset, 'top', True)

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
        test = self.plinkio._process_pedline(child, self.dataset, 'top', True)

        # define smarter_id
        smarter_id = "ITOA-TEX-000000001"

        self.assertEqual(test[1], smarter_id)
        self.assertEqual(test[2], "0")
        self.assertEqual(test[3], "0")

    def test_update_pedfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.ped"
            self.plinkio.update_pedfile(
                str(outfile), self.dataset, 'top', True)

            # now open outputfile and test stuff
            test = TextPlinkIO(
                mapfile=str(DATA_DIR / "plinktest.map"),
                pedfile=str(outfile))

            # assert two records written
            self.assertEqual(len(list(test.read_pedfile())), 2)

    def test_update_pedfile_no_insert(self):
        """Test no sample creating while processing genotypes"""

        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.ped"
            self.plinkio.update_pedfile(
                str(outfile), self.dataset, 'top', False)

            with open(outfile) as handle:
                data = handle.read()

            # outfile is an empty
            self.assertEqual(data, '')

        # no sample created
        self.assertEqual(SampleSheep.objects.count(), 0)


class BinaryPlinkIOTest(
        VariantsMixin, SmarterIDMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.plinkio = BinaryPlinkIO(
            prefix=str(DATA_DIR / "plinktest"),
            species="Sheep")

        self.src_assembly = AssemblyConf(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

        # read info from map
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(src_assembly=self.src_assembly)

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

        test = self.plinkio._process_pedline(line, dataset, 'top', True)

        self.assertEqual(reference, test)


class IlluminaReportIOMap(VariantsMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.plinkio = IlluminaReportIO(
            snpfile=str(DATA_DIR / "snplist.txt"),
            report=str(DATA_DIR / "finalreport.txt"),
            species="Sheep")

        self.plinkio.read_snpfile()

        self.src_assembly = AssemblyConf(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

    def test_read_snpfile(self):
        self.assertIsInstance(self.plinkio.mapdata, list)
        self.assertEqual(len(self.plinkio.mapdata), 2)
        for record in self.plinkio.mapdata:
            self.assertIsInstance(record, tuple)

    def test_fetch_coordinates(self):
        self.plinkio.fetch_coordinates(src_assembly=self.src_assembly)

        self.assertIsInstance(self.plinkio.src_locations, list)
        self.assertEqual(len(self.plinkio.src_locations), 2)
        self.assertIsInstance(self.plinkio.dst_locations, list)
        self.assertEqual(len(self.plinkio.dst_locations), 2)

        self.assertIsInstance(self.plinkio.filtered, set)
        self.assertEqual(len(self.plinkio.filtered), 0)

        for idx, record in enumerate(self.plinkio.dst_locations):
            self.assertIsInstance(record, Location)

    def test_update_mapfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            # this is the temporary output file
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.map"

            self.plinkio.fetch_coordinates(src_assembly=self.src_assembly)
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
        VariantsMixin, SmarterIDMixin, SupportedChipMixin, MongoMockMixin,
        unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.dataset = Dataset.objects.get(file="test.zip")

        self.plinkio = IlluminaReportIO(
            snpfile=str(DATA_DIR / "snplist.txt"),
            report=str(DATA_DIR / "finalreport.txt"),
            species="Sheep")

        self.src_assembly = AssemblyConf(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")

        # read info from map
        self.plinkio.read_snpfile()
        self.plinkio.fetch_coordinates(src_assembly=self.src_assembly)

        # read first line of ped file
        self.lines = list(self.plinkio.read_reportfile(breed="TEX"))

    def test_read_reportfile(self):
        test = self.plinkio.read_reportfile(breed="TEX")
        self.assertIsInstance(test, types.GeneratorType)

        # consume data and count rows
        test = list(test)
        self.assertEqual(len(test), 2)

    def test_read_reportfile_no_fid(self):
        """Try to determine fid from database"""

        # create two fake samples to colled fid relying on database
        for i in range(2):
            sample = SampleSheep(
                original_id=f"{i+1}",
                country="Italy",
                breed="Texel",
                breed_code="TEX",
                species="Sheep",
                dataset=self.dataset,
                type_="background",
                chip_name=self.chip_name
            )
            sample.save()

        test = self.plinkio.read_reportfile(dataset=self.dataset)
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

        test = self.plinkio._process_pedline(line, dataset, 'ab', True)

        self.assertEqual(reference, test)

    def test_update_pedfile(self):
        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "plinktest_updated.ped"
            self.plinkio.update_pedfile(
                str(outfile), dataset, 'ab', breed="TEX", create_samples=True)

            # now open outputfile and test stuff
            test = TextPlinkIO(
                mapfile=str(DATA_DIR / "plinktest.map"),
                pedfile=str(outfile))

            # assert two records written
            self.assertEqual(len(list(test.read_pedfile())), 2)


class AffyMixin():
    """Common stuff for affymetrix tests"""

    # load a custom fixture for this class
    variant_fixture = "affy_variants.json"

    # custom chip
    chip_name = "AffymetrixAxiomOviCan"

    def setUp(self):
        super().setUp()

        # source and destination assemblies
        self.src_assembly = AssemblyConf(
            version="Oar_v4.0", imported_from="affymetrix")
        self.dst_assembly = AssemblyConf(
            version="Oar_v3.1", imported_from="SNPchiMp v.3")


class AffyPlinkIOMapTest(
        AffyMixin, VariantsMixin, MongoMockMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.plinkio = AffyPlinkIO(
            prefix=str(DATA_DIR / "affytest"),
            species="Sheep",
            chip_name=self.chip_name
        )

    def test_read_mapfile(self):
        self.plinkio.read_mapfile()
        self.assertIsInstance(self.plinkio.mapdata, list)
        self.assertEqual(len(self.plinkio.mapdata), 4)
        for record in self.plinkio.mapdata:
            self.assertIsInstance(record, MapRecord)

    def test_fetch_coordinates(self):
        self.plinkio.read_mapfile()
        self.plinkio.fetch_coordinates(
            src_assembly=self.src_assembly,
            dst_assembly=self.dst_assembly,
            search_field='probeset_id',
            chip_name=self.chip_name
        )

        self.assertIsInstance(self.plinkio.src_locations, list)
        self.assertEqual(len(self.plinkio.src_locations), 4)
        self.assertIsInstance(self.plinkio.dst_locations, list)
        self.assertEqual(len(self.plinkio.dst_locations), 4)

        self.assertIsInstance(self.plinkio.filtered, set)
        self.assertEqual(len(self.plinkio.filtered), 2)

        # assert filtered items
        self.assertIn(2, self.plinkio.filtered)
        self.assertIn(3, self.plinkio.filtered)

        for idx, record in enumerate(self.plinkio.dst_locations):
            if idx in self.plinkio.filtered:
                self.assertIsNone(record)
            else:
                self.assertIsInstance(record, Location)

    def test_update_mapfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "affytest_updated.map"
            self.plinkio.read_mapfile()
            self.plinkio.fetch_coordinates(
                src_assembly=self.src_assembly,
                dst_assembly=self.dst_assembly,
                search_field='probeset_id',
                chip_name=self.chip_name
            )
            self.plinkio.update_mapfile(str(outfile))

            # now open outputfile and test stuff
            test = TextPlinkIO(mapfile=str(outfile))
            test.read_mapfile()

            # one snp cannot be mapped
            self.assertEqual(len(test.mapdata), 2)

            for record in test.mapdata:
                variant = VariantSheep.objects(name=record.name).get()
                location = variant.get_location(
                    version="Oar_v3.1", imported_from="SNPchiMp v.3")
                self.assertEqual(location.chrom, record.chrom)
                self.assertEqual(location.position, record.position)


class AffyPlinkIOPedTest(
        AffyMixin, VariantsMixin, SmarterIDMixin, MongoMockMixin,
        unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.plinkio = AffyPlinkIO(
            prefix=str(DATA_DIR / "affytest"),
            species="Sheep",
            chip_name="AffymetrixAxiomOviCan"
        )

        # read info from map
        self.plinkio.read_mapfile()

        # collect info for source and destination assemblies
        self.plinkio.fetch_coordinates(
            src_assembly=self.src_assembly,
            dst_assembly=self.dst_assembly,
            search_field='probeset_id',
            chip_name=self.chip_name
        )

        # read ped files
        self.lines = list(self.plinkio.read_pedfile(breed="TEX"))

    def test_assert_filtered(self):
        self.assertEqual(self.plinkio.filtered, {2, 3})

    def test_read_pedfile(self):
        test = self.plinkio.read_pedfile(breed="TEX")
        self.assertIsInstance(test, types.GeneratorType)

        # consume data and count rows
        test = list(test)
        self.assertEqual(len(test), 2)

    def test_read_pedfile_no_fid(self):
        """Try to determine fid from database"""

        # create two fake samples to colled fid relying on database
        for sample_name in ["test-one", "test-two"]:
            sample = SampleSheep(
                original_id=sample_name,
                country="Italy",
                breed="Texel",
                breed_code="TEX",
                species="Sheep",
                dataset=self.dataset,
                type_="background",
                chip_name=self.chip_name
            )
            sample.save()

        test = self.plinkio.read_pedfile(dataset=self.dataset)
        self.assertIsInstance(test, types.GeneratorType)

        # consume data and count rows
        test = list(test)
        self.assertEqual(len(test), 2)

    def test_process_pedline(self):
        # define reference
        reference = [
            'TEX', 'ITOA-TEX-000000001', '0', '0', '0', -9,
            'A', 'G', 'A', 'A']

        # get a line for testing
        line = self.lines[0]

        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        test = self.plinkio._process_pedline(line, dataset, 'affymetrix', True)

        self.assertEqual(reference, test)

    def test_update_pedfile(self):
        # get a dataset
        dataset = Dataset.objects(file="test.zip").get()

        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "affytes_updated.ped"
            self.plinkio.update_pedfile(
                str(outfile),
                dataset,
                'affymetrix',
                breed="TEX",
                create_samples=True)

            # now open outputfile and test stuff
            test = TextPlinkIO(
                mapfile=str(DATA_DIR / "plinktest.map"),
                pedfile=str(outfile))

            # assert two records written
            self.assertEqual(len(list(test.read_pedfile())), 2)


class AffyReportIOMapTest(
        AffyMixin, VariantsMixin, MongoMockMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.plinkio = AffyReportIO(
            report=DATA_DIR / "affyreport.txt",
            species="Sheep",
            chip_name=self.chip_name
        )

    def test_mapdata(self):
        """Test for mapdata after reading reportfile"""

        self.plinkio.read_reportfile()
        self.assertIsInstance(self.plinkio.mapdata, list)
        self.assertEqual(len(self.plinkio.mapdata), 3)
        for record in self.plinkio.mapdata:
            self.assertIsInstance(record, MapRecord)

    def test_fetch_coordinates(self):
        self.plinkio.read_reportfile()
        self.plinkio.fetch_coordinates(
            src_assembly=self.src_assembly,
            dst_assembly=self.dst_assembly,
            search_field='probeset_id',
            chip_name=self.chip_name
        )

        self.assertIsInstance(self.plinkio.src_locations, list)
        self.assertEqual(len(self.plinkio.src_locations), 3)
        self.assertIsInstance(self.plinkio.dst_locations, list)
        self.assertEqual(len(self.plinkio.dst_locations), 3)

        self.assertIsInstance(self.plinkio.filtered, set)
        self.assertEqual(len(self.plinkio.filtered), 2)

        # assert filtered items
        self.assertIn(1, self.plinkio.filtered)
        self.assertIn(2, self.plinkio.filtered)

        for idx, record in enumerate(self.plinkio.dst_locations):
            if idx in self.plinkio.filtered:
                self.assertIsNone(record)
            else:
                self.assertIsInstance(record, Location)

    def test_update_mapfile(self):
        # create a temporary directory using the context manager
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = pathlib.Path(tmpdirname) / "affytest_updated.map"
            self.plinkio.read_reportfile()
            self.plinkio.fetch_coordinates(
                src_assembly=self.src_assembly,
                dst_assembly=self.dst_assembly,
                search_field='probeset_id',
                chip_name=self.chip_name
            )
            self.plinkio.update_mapfile(str(outfile))

            # now open outputfile and test stuff
            test = TextPlinkIO(mapfile=str(outfile))
            test.read_mapfile()

            # one snp cannot be mapped
            self.assertEqual(len(test.mapdata), 1)

            for record in test.mapdata:
                variant = VariantSheep.objects(name=record.name).get()
                location = variant.get_location(
                    version="Oar_v3.1", imported_from="SNPchiMp v.3")
                self.assertEqual(location.chrom, record.chrom)
                self.assertEqual(location.position, record.position)


if __name__ == '__main__':
    unittest.main()
