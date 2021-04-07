#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 17:32:28 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import unittest
import pathlib

from mongoengine import connect, disconnect, connection

from src.features.smarterdb import (
    VariantSheep, Location, DB_ALIAS, SampleSheep, Breed, Counter,
    SmarterDBException, getSmarterId)


# set data dir (like os.dirname(__file__)) + "fixtures"
DATA_DIR = pathlib.Path(__file__).parent / "fixtures"


class MongoMock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        connect(
            'mongoenginetest',
            host='mongomock://localhost',
            alias=DB_ALIAS)

        cls.connection = connection.get_db(alias=DB_ALIAS)

    @classmethod
    def tearDownClass(cls):
        disconnect()


class VariantMixin():
    @classmethod
    def setUpClass(cls):
        with open(DATA_DIR / "variant.json") as handle:
            cls.data = json.load(handle)

        super().setUpClass()


class LocationTestCase(VariantMixin, MongoMock):
    def setUp(self):
        location = self.data["locations"][1]
        self.location = Location.from_json(json.dumps(location))

    def test_illumina_top(self):
        self.assertEqual(self.location.illumina_top, "A/G")

        # assert the same but chaning illumina_strand
        self.location.illumina_strand = "TOP"
        self.assertEqual(self.location.illumina_top, "A/G")

        self.location.illumina_strand = "BOT"
        self.assertEqual(self.location.illumina_top, "T/C")

    def test_illumina_top_not_managed(self):
        self.location.illumina_strand = "bottom"

        self.assertRaisesRegex(
            SmarterDBException,
            "not managed",
            getattr,
            self.location,
            "illumina_top"
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
        location.illumina_strand = "BOT"

        self.assertNotEqual(self.location, location)

        # other changes returns True
        location.illumina_strand = "forward"
        location.illumina_forward = "A/G"
        location.strand = "top"

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


class VariantSheepTestCase(VariantMixin, MongoMock):
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


class SmarterIDMixin():
    """Common set up for classes which require a smarter id to work properly"""
    @classmethod
    def setUpClass(cls):
        # need to define a breed in order to get a smarter id
        breed = Breed(
            species="Sheep",
            name="Texel",
            code="TEX"
        )
        breed.save()

        # need also a counter object for sheep and goat
        counter = Counter(
            pk="sampleSheep",
            sequence_value=0
        )
        counter.save()

        counter = Counter(
            pk="sampleGoat",
            sequence_value=0
        )
        counter.save()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        # delete breeds and counter objects
        Breed.objects().delete()
        Counter.objects().delete()

        super().tearDownClass()


class GetSmarterIdTestCase(SmarterIDMixin, MongoMock):
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


class SampleSheepTestCase(SmarterIDMixin, MongoMock):
    def setUp(self):
        self.smarter_id = None
        self.original_id = "TEST"

        self.sample = SampleSheep(
            original_id=self.original_id,
            smarter_id=self.smarter_id
        )

    def test__str(self):
        self.assertEqual(
            str(self.sample),
            f"{self.smarter_id} ({self.original_id})"
        )

    def test_save(self):
        # need country, breed and species in order to get a smarter_id
        self.sample.country = "Italy"
        self.sample.breed = "Texel"
        self.sample.species = "Sheep"

        # save sample in db
        self.sample.save()

        # this will be the reference smarter_id
        reference = "ITOA-TEX-000000001"

        self.assertEqual(self.sample.smarter_id, reference)


if __name__ == '__main__':
    unittest.main()
