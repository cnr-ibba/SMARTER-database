#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 17:32:28 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import unittest
import pathlib
from unittest.mock import patch

from src.features.smarterdb import (
    VariantSheep, Location, SampleSheep,
    SmarterDBException, getSmarterId, Breed, get_or_create_breed, Dataset,
    BreedAlias, get_or_create_sample, SEX)

from ..common import MongoMockMixin, SmarterIDMixin

# set data dir (like os.dirname(__file__)) + "fixtures"
DATA_DIR = pathlib.Path(__file__).parents[1] / "fixtures"


class BreedTestCase(MongoMockMixin, unittest.TestCase):
    def setUp(self):
        # createing a sample breed
        self.breed = Breed(
            species="Sheep",
            name="Texel",
            code="TEX",
            aliases=[],
            n_individuals=0
        )
        self.breed.save()

        # need a dataset for certain tests
        self.dataset = Dataset(
            file="test.zip",
            country="Italy",
            species="Sheep",
            contents=[
                "plinktest.map",
                "plinktest.ped",
                "snplist.txt",
                "finalreport.txt"
            ]
        )
        self.dataset.save()

    def tearDown(self):
        # drop all created breed
        Breed.objects.delete()
        Dataset.objects.delete()

        super().tearDown()

    @patch.object(Breed, 'save')
    def test_get_breed(self, mocked):
        """Getting an existent breed doesn't modify database"""

        breed, modified = get_or_create_breed(
            species='Sheep',
            name="Texel",
            code="TEX"
        )

        self.assertFalse(modified)
        self.assertIsInstance(breed, Breed)
        self.assertFalse(mocked.called)

    @patch.object(Breed, 'save')
    def test_update_aliases(self, mocked):
        """Add a new alias update breed"""

        alias = BreedAlias(
            fid="TEXEL_IT",
            dataset=self.dataset
        )

        breed, modified = get_or_create_breed(
            species='Sheep',
            name="Texel",
            code="TEX",
            aliases=[alias]
        )

        self.assertTrue(modified)
        self.assertIsInstance(breed, Breed)
        self.assertTrue(mocked.called)
        self.assertEqual(
            breed.aliases, [alias])

    def test_create_breed(self):
        """Create a new breed object"""

        alias = BreedAlias(
            fid="CREOLE_IT",
            dataset=self.dataset
        )

        breed, modified = get_or_create_breed(
            species='Sheep',
            name="Creole",
            code="CRL",
            aliases=[alias]
        )

        self.assertTrue(modified)
        self.assertIsInstance(breed, Breed)
        self.assertEqual(
            breed.aliases, [alias])
        self.assertEqual(Breed.objects.count(), 2)


class VariantMixin():
    @classmethod
    def setUpClass(cls):
        with open(DATA_DIR / "affy_variants.json") as handle:
            cls.data = json.load(handle)[0]

        with open(DATA_DIR / "affy_variants.json") as handle:
            cls.affy_data = json.load(handle)[2]

        super().setUpClass()


class LocationTestCase(VariantMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        location = self.data["locations"][1]
        self.location = Location.from_json(json.dumps(location))

        affy_location = self.affy_data["locations"][2]
        self.affy_location = Location.from_json(json.dumps(affy_location))

    def test_illumina_top(self):
        self.assertEqual(self.location.illumina_top, "A/G")

        # assert the same but chaning illumina_strand
        self.location.illumina_strand = "TOP"
        self.assertEqual(self.location.illumina_top, "T/C")

        self.location.illumina_strand = "top"
        self.assertEqual(self.location.illumina_top, "T/C")

        self.location.illumina_strand = "BOT"
        self.assertEqual(self.location.illumina_top, "A/G")

        self.location.illumina_strand = "bottom"
        self.assertEqual(self.location.illumina_top, "A/G")

    def test_illumina_top_setter(self):
        location = Location.from_json(
            json.dumps({
                "ss_id": "ss836353361",
                "version": "Oar_v3.1",
                "chrom": "1",
                "position": 121169033,
                "alleles": "A/G",
                "illumina_top": "A/G",
                "illumina_forward": "T/C",
                "illumina_strand": "top",
                "strand": "reverse",
                "imported_from": "SNPchiMp v.3",
                "consequences": []
            })
        )

        self.assertEqual(location.illumina, "A/G")

        # assert the same but chaning illumina_strand
        location.illumina_strand = "TOP"
        location.illumina_top = "A/G"
        self.assertEqual(location.illumina, "A/G")

        location.illumina_strand = "top"
        location.illumina_top = "A/G"
        self.assertEqual(location.illumina, "A/G")

        location.illumina_strand = "BOT"
        location.illumina_top = "A/G"
        self.assertEqual(location.illumina, "T/C")

        location.illumina_strand = "bottom"
        location.illumina_top = "A/G"
        self.assertEqual(location.illumina, "T/C")

    def test_illumina_strand_not_defined(self):
        """With no illumina_strand, we suppose that illumina_top is the
        same of illumina"""

        # with no illumina_strand, we suppose to have illumina code
        self.location.illumina_strand = None
        self.assertEqual(self.location.illumina_top, self.location.illumina)

        self.location.illumina_top = "A/T"
        self.assertEqual(self.location.illumina, "A/T")

    def test_illumina_top_not_managed(self):
        self.location.illumina_strand = "reverse"

        self.assertRaisesRegex(
            SmarterDBException,
            "not managed",
            getattr,
            self.location,
            "illumina_top"
        )

        self.assertRaisesRegex(
            SmarterDBException,
            "not managed",
            setattr,
            self.location,
            "illumina_top",
            "A/G"
        )

    def test__eq(self):
        location = self.data["locations"][1]
        location = Location.from_json(json.dumps(location))

        self.assertEqual(self.location, location)

        # assert not equal relying positions
        location.chrom = "1"
        location.position = 5870057

        self.assertNotEqual(self.location, location)

        location.chrom = "15"
        location.position = 1

        self.assertNotEqual(self.location, location)

        # assert not equal relying illumina_top (illumina_strand)
        location.chrom = "15"
        location.position = 5870057
        location.illumina_strand = "TOP"

        self.assertNotEqual(self.location, location)

        # other changes returns True
        location.illumina_strand = "bottom"
        location.illumina_forward = "A/G"
        location.strand = "forward"

        self.assertEqual(self.location, location)

    def test__str(self):
        self.assertEqual(
            str(self.location),
            "(SNPchiMp v.3:Oar_v3.1) 15:5870057 [A/G]"
        )

    def test_is_top(self):
        for genotype in ["A/A", "A/G", "G/A", "G/G", "0/0"]:
            genotype = genotype.split("/")

            self.assertTrue(
                self.location.is_top(genotype),
                msg=f"{genotype} is not in top coordinates!"
            )

        # is not in not if contains an allele not in top format
        for genotype in ["T/C", "A/C", "G/T"]:
            self.assertFalse(
                self.location.is_top(genotype),
                msg=f"{genotype} is in top coordinates!"
            )

    def test_is_forward(self):
        for genotype in ["T/C", "T/T", "C/T", "C/C", "0/0"]:
            genotype = genotype.split("/")

            self.assertTrue(
                self.location.is_forward(genotype),
                msg=f"{genotype} is not in forward coordinates!"
            )

        # is not in not if contains an allele not in top format
        for genotype in ["A/A", "A/G", "G/A", "G/G"]:
            self.assertFalse(
                self.location.is_forward(genotype),
                msg=f"{genotype} is in forward coordinates!"
            )

    def test_forward2top(self):
        """Test forward to top conversion"""

        forwards = ["T/C", "T/T", "C/T", "C/C", "0/0"]
        tops = ["A/G", "A/A", "G/A", "G/G", "0/0"]

        for i, genotype in enumerate(forwards):
            reference = tops[i].split("/")
            genotype = genotype.split("/")

            test = self.location.forward2top(genotype)
            self.assertEqual(reference, test)

    def test_forward2top_error(self):
        """Test exception with an allele not in forward coding"""
        self.assertRaisesRegex(
            SmarterDBException,
            "is not in forward coding",
            self.location.forward2top,
            ["A", "T"]
        )

    def test_is_ab(self):
        for genotype in ["A/A", "A/B", "B/A", "B/B", "-/-"]:
            genotype = genotype.split("/")

            self.assertTrue(
                self.location.is_ab(genotype),
                msg=f"{genotype} is not in ab coordinates!"
            )

        # is not in not if contains an allele not in top format
        # HINT: "A/A" is a special case since cam be top or AB in the same time
        for genotype in ["T/C", "A/C", "G/T", "G/G", "A/G", "0/0"]:
            self.assertFalse(
                self.location.is_top(genotype),
                msg=f"{genotype} is in ab coordinates!"
            )

    def test_ab2top(self):
        """Test ab to top conversion"""

        ab = ["A/B", "A/A", "B/A", "B/B", "-/-"]
        tops = ["A/G", "A/A", "G/A", "G/G", "0/0"]

        for i, genotype in enumerate(ab):
            reference = tops[i].split("/")
            genotype = genotype.split("/")

            test = self.location.ab2top(genotype)
            self.assertEqual(reference, test)

    def test_ab2top_error(self):
        """Test exception with an allele not in ab coding"""
        self.assertRaisesRegex(
            SmarterDBException,
            "is not in ab coding",
            self.location.ab2top,
            ["A", "T"]
        )

    def test_is_affy(self):
        for genotype in ["T/C", "T/T", "C/T", "C/C", "-/-"]:
            genotype = genotype.split("/")

            self.assertTrue(
                self.affy_location.is_affymetrix(genotype),
                msg=f"{genotype} is not in affymetrix coordinates!"
            )

        # is not in not if contains an allele not in top format
        for genotype in ["A/A", "A/G", "G/A", "G/G"]:
            self.assertFalse(
                self.location.is_forward(genotype),
                msg=f"{genotype} is in affymetrix coordinates!"
            )

    def test_affy2top(self):
        """Test affymetrix to top conversion"""

        affymetrixs = ["T/C", "T/T", "C/T", "C/C", "-/-"]
        tops = ["A/G", "A/A", "G/A", "G/G", "0/0"]

        for i, genotype in enumerate(affymetrixs):
            reference = tops[i].split("/")
            genotype = genotype.split("/")

            test = self.affy_location.affy2top(genotype)
            self.assertEqual(reference, test)

    def test_affy2top_error(self):
        """Test exception with an allele not in affymetrix coding"""
        self.assertRaisesRegex(
            SmarterDBException,
            "is not in affymetrix coding",
            self.affy_location.affy2top,
            ["A", "T"]
        )


class VariantSheepTestCase(VariantMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        self.variant = VariantSheep.from_json(json.dumps(self.data))

    def test__str(self):
        self.assertEqual(
            str(self.variant),
            "name='250506CS3900065000002_1238.1', rs_id='rs55630613'"
        )

    def test_location(self):
        "get a specific location from VariantSheep"

        reference = self.data["locations"][1]
        reference = Location.from_json(json.dumps(reference))

        test = self.variant.get_location(
            version="Oar_v3.1",
            imported_from='SNPchiMp v.3'
        )

        self.assertEqual(reference, test)

    def test_get_location_index(self):
        "get a specific location from VariantSheep"

        index = self.variant.get_location_index(
            version="Oar_v3.1",
            imported_from='SNPchiMp v.3'
        )

        self.assertEqual(index, 1)

    def test_no_location(self):
        "Search for a location not present in database raise exception"

        self.assertRaisesRegex(
            SmarterDBException,
            "Couldn't determine a unique location for",
            self.variant.get_location,
            version="Oar_v4.0",
            imported_from='SNPchiMp v.3'
        )

    def test_no_location_index(self):
        "Search for a location not present in database raise exception"

        self.assertRaisesRegex(
            SmarterDBException,
            "is not in locations",
            self.variant.get_location_index,
            version="Oar_v4.0",
            imported_from='SNPchiMp v.3'
        )


class GetSmarterIdTestCase(SmarterIDMixin, MongoMockMixin, unittest.TestCase):
    """Testing getSmarterId function"""

    def test_missing_parameters(self):
        """calling functions with missing parameters raise exception"""

        with self.assertRaisesRegex(
                SmarterDBException,
                "species, country and breed should be defined when calling",
                msg="SmarterDBException not raised for empty species"):
            getSmarterId(
                None,
                "Italy",
                "Texel",
                self.connection
            )

        with self.assertRaisesRegex(
                SmarterDBException,
                "species, country and breed should be defined when calling",
                msg="SmarterDBException not raised for empty country"):
            getSmarterId(
                "Sheep",
                None,
                "Texel",
                self.connection
            )

        with self.assertRaisesRegex(
                SmarterDBException,
                "species, country and breed should be defined when calling",
                msg="SmarterDBException not raised for empty breed"):
            getSmarterId(
                "Sheep",
                "Italy",
                None,
                self.connection
            )

    def test_species_not_managed(self):
        with self.assertRaisesRegex(
                SmarterDBException,
                "not managed"):
            getSmarterId(
                "Cow",
                "Italy",
                "Frisona",
                self.connection
            )


class SampleSheepTestCase(SmarterIDMixin, MongoMockMixin, unittest.TestCase):
    def setUp(self):
        # this will be the reference smarter_id
        self.smarter_id = "ITOA-TEX-000000001"
        self.original_id = "TEST"

        # fetch some values from database
        self.dataset = Dataset.objects.get(file="test.zip")
        self.breed = Breed.objects.get(species="Sheep", code="TEX")

        # this is required to create a sample
        self.country = "Italy"

        # additional sample fields
        self.chip_name = "IlluminaOvineSNP50"
        self.sex = SEX.MALE
        self.alias = "TEST-ALIAS"

    def tearDown(self):
        SampleSheep.objects().delete()

        super().tearDown()

    def create_sample(self):
        """Create a sample instance in mongodb"""

        self.sample = SampleSheep(
            original_id=self.original_id,
            smarter_id=None
        )

        # need country, breed and species in order to get a smarter_id
        self.sample.country = self.country
        self.sample.breed = "Texel"
        self.sample.species = "Sheep"

        # save sample in db
        self.sample.save()

        return self.sample

    def test__str(self):
        self.create_sample()

        self.assertEqual(
            str(self.sample),
            f"{self.smarter_id} (Texel)"
        )

    def test_save_smarter_id(self):
        self.create_sample()

        self.assertEqual(self.sample.smarter_id, self.smarter_id)

    def test_get_or_create_sample(self):
        # creating sample first
        sample, created = get_or_create_sample(
            SampleSheep,
            self.original_id,
            self.dataset,
            self.breed,
            self.country,
            self.chip_name,
            self.sex,
            self.alias
        )

        self.assertIsInstance(sample, SampleSheep)
        self.assertEqual(sample.smarter_id, self.smarter_id)
        self.assertEqual(SampleSheep.objects.count(), 1)
        self.assertTrue(created)

        # calling the same function again, retrieve the same object
        sample, created = get_or_create_sample(
            SampleSheep,
            self.original_id,
            self.dataset,
            self.breed,
            self.country,
            self.chip_name,
            self.sex,
            self.alias
        )

        self.assertIsInstance(sample, SampleSheep)
        self.assertEqual(sample.smarter_id, self.smarter_id)
        self.assertEqual(SampleSheep.objects.count(), 1)
        self.assertFalse(created)


class SEXTestCase(unittest.TestCase):
    def is_male(self, test):
        self.assertEqual(test, SEX.MALE)
        self.assertEqual(test._value_, 1)
        self.assertEqual(str(test), 'Male')

    def is_female(self, test):
        self.assertEqual(test, SEX.FEMALE)
        self.assertEqual(test._value_, 2)
        self.assertEqual(str(test), 'Female')

    def is_unknown(self, test):
        self.assertEqual(test, SEX.UNKNOWN)
        self.assertEqual(test._value_, 0)
        self.assertEqual(str(test), 'Unknown')

    def test_get_by_num(self):
        test = SEX(1)
        self.is_male(test)

        test = SEX(2)
        self.is_female(test)

        test = SEX(0)
        self.is_unknown(test)

    def test_get_by_str(self):
        test = SEX.from_string('M')
        self.is_male(test)

        test = SEX.from_string('male')
        self.is_male(test)

        test = SEX.from_string('1')
        self.is_male(test)

        test = SEX.from_string('f')
        self.is_female(test)

        test = SEX.from_string('Female')
        self.is_female(test)

        test = SEX.from_string('2')
        self.is_female(test)

        test = SEX.from_string('unmanaged')
        self.is_unknown(test)

    def test_get_by_str_raise(self):
        self.assertRaisesRegex(
            SmarterDBException,
            "Provided value should be a 'str' type",
            SEX.from_string,
            1
        )


if __name__ == '__main__':
    unittest.main()
