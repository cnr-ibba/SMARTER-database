#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 16:21:35 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import logging
import pathlib
import mongoengine

from enum import Enum
from typing import List, Tuple, Union

from pymongo import database, ReturnDocument, MongoClient
from dotenv import find_dotenv, load_dotenv

from .utils import get_project_dir, UnknownCountry, countries

SPECIES2CODE = {
    "Sheep": "OA",
    "Goat": "CH"
}

SMARTERDB = "smarter"
DB_ALIAS = "smarterdb"
CLIENT = None

# Get an instance of a logger
logger = logging.getLogger(__name__)


class SmarterDBException(Exception):
    pass


def global_connection(database_name: str = SMARTERDB) -> MongoClient:
    """
    Establish a connection to the SMARTER database. Reads environment
    parameters using :py:func:`load_dotenv`, returns a MongoClient object.

    Parameters
    ----------
    database_name : str, optional
        The smarter database. The default is 'smarter'.

    Returns
    -------
    CLIENT : MongoClient
        a mongoclient instance.
    """

    global CLIENT

    if not CLIENT:
        # find .env automagically by walking up directories until it's found,
        # then load up the .env entries as environment variables
        load_dotenv(find_dotenv())

        # track connection somewhere
        CLIENT = mongoengine.connect(
            database_name,
            username=os.getenv("MONGODB_SMARTER_USER"),
            password=os.getenv("MONGODB_SMARTER_PASS"),
            host=os.getenv("MONGODB_SMARTER_HOST", default="localhost"),
            port=os.getenv("MONGODB_SMARTER_PORT", default=27017),
            authentication_source='admin',
            alias=DB_ALIAS,
            uuidRepresentation="standard")

    return CLIENT


def complement(genotype: str) -> str:
    """
    Return reverse complement for a base call

    Parameters
    ----------
    genotype : str
        A base call (one from `A`, `T`, `G`, `C`).

    Returns
    -------
    result : str
        The reverse complement of the base call.

    """
    bases = {
        "A": "T",
        "T": "A",
        "C": "G",
        "G": "C",
        "/": "/"
    }

    result = ""

    for base in genotype:
        result += bases[base]

    return result


class SmarterInfo(mongoengine.Document):
    """A class to track database status informations"""

    id = mongoengine.StringField(primary_key=True)
    version = mongoengine.StringField(required=True)
    """The SMARTER-database version"""

    working_assemblies = mongoengine.DictField()
    """A dictionary in which managed assemblies are tracked"""

    plink_specie_opt = mongoengine.DictField()
    """The plink parameters used to generate the final genotype dataset"""

    last_updated = mongoengine.DateTimeField()
    """When the SMARTER-database was updated for the last time"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'smarterInfo'
    }

    def __str__(self):
        return f"{self.id}: {self.version} ({self.last_updated})"


class Counter(mongoengine.Document):
    """A class to deal with counter collection (created when initializing
    smarter database) and used to define SMARTER IDs
    """

    id = mongoengine.StringField(primary_key=True)
    sequence_value = mongoengine.IntField(required=True, default=0)

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'counters'
    }

    def __str__(self):
        return f"{self.id}: {self.sequence_value}"


class Country(mongoengine.Document):
    """A helper class to deal with countries object. Each record is created
    after data import, when database status is updated"""

    alpha_2 = mongoengine.StringField(
        required=True, unique=True, min_length=2, max_length=2)
    """Country 2 letter code (used to derive SMARTER IDs)"""

    alpha_3 = mongoengine.StringField(
        required=True, unique=True, min_length=3, max_length=3)
    """Country 3 letter code"""

    name = mongoengine.StringField(required=True, unique=True)
    """The Country name"""

    numeric = mongoengine.IntField(unique=True)
    """The country numeric code"""

    official_name = mongoengine.StringField()
    """Country official name"""

    species = mongoengine.ListField(mongoengine.StringField())
    """The sample species find within this country"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'countries'
    }

    def __init__(self, name: str = None, *args, **kwargs):
        # fix species type if necessary
        if "species" in kwargs:
            if isinstance(kwargs["species"], str):
                kwargs["species"] = [kwargs["species"]]

        # initialize base object
        super(Country, self).__init__(*args, name=name, **kwargs)

        if not self.id and name:
            logger.warning(f"Creating country object for '{name}'")

            # get a country object
            if name.lower() == "unknown":
                country = UnknownCountry()
            else:
                country = countries.get(name=name)

            if country:
                self.alpha_2 = country.alpha_2
                self.alpha_3 = country.alpha_3
                self.numeric = country.numeric

            if hasattr(country, "official_name"):
                self.official_name = country.official_name

    def __str__(self):
        return f"{self.name} ({self.alpha_2})"


class SupportedChip(mongoengine.Document):
    """A class to deal with SMARTER-database managed chips"""

    name = mongoengine.StringField(required=True, unique=True)
    """The chip identifier"""

    species = mongoengine.StringField(required=True)
    """The species for which a chip is defined"""

    manufacturer = mongoengine.StringField()
    """Who created the chip"""

    n_of_snps = mongoengine.IntField()
    """How many SNPs are described within this chip"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'supportedChips'
    }

    def __str__(self):
        return f"'{self.name}' ({self.species})"


class BreedAlias(mongoengine.EmbeddedDocument):
    """Required to describe the breed and code used in a certain dataset in
    order to resolve the final breed to be used in SMARTER-database"""

    fid = mongoengine.StringField(required=True)
    """The breed Family ID used in genotype file"""

    dataset = mongoengine.ReferenceField(
        'Dataset',
        db_field="dataset_id")
    """The dataset ``ObjectID`` in which this BreedAlias is used"""

    country = mongoengine.StringField()
    """The country of the breed in the dataset. Used in multi country
    datasets"""

    def __str__(self):
        return f"{self.fid}: {self.dataset}"


class Breed(mongoengine.Document):
    species = mongoengine.StringField(required=True)
    """The breed species. Should be one of ``Goat`` or ``Sheep``"""

    name = mongoengine.StringField(required=True)
    """The breed name"""

    code = mongoengine.StringField(required=True)
    """The breed code"""

    aliases = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(BreedAlias))
    """A list of :py:class:`BreedAlias` objects. Required to determine the
    SMARTER-database breed from the genotype file (which can use a different
    breed name or code)"""

    n_individuals = mongoengine.IntField()
    """How many samples are the same breed"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'breeds',
        'indexes': [
            {
                'fields': [
                    "species",
                    "code"
                ],
                'unique': True,
                'collation': {'locale': 'en', 'strength': 1}
            },
            {
                'fields': [
                    "species",
                    "name"
                ],
                'unique': True,
                'collation': {'locale': 'en', 'strength': 1}
            }
        ]
    }

    def __str__(self):
        return f"{self.name} ({self.code}) {self.species}"


def get_or_create_breed(
        species_class: str, name: str, code: str,
        aliases: List[BreedAlias] = []) -> Tuple[Breed, bool]:
    """
    Get a Breed instance or create a new one (or update a breed adding a new
    :py:class:`BreedAlias`)

    Parameters
    ----------
    species_class : str
        The class of the species (should be 'Goat' or 'Sheep')
    name : str
        The breed full name.
    code : str
        The breed code (unique in Sheep and Goats collections).
    aliases : list, optional
        A list of :py:class:`BreedAlias` objects. The default is [].

    Raises
    ------
    SmarterDBException
        Raised if the breed is not Unique.

    Returns
    -------
    breed : Breed
        A :py:class:`Breed` instance.
    modified : bool
        True is breed is created (or alias updated).
    """

    logger.debug(f"Checking: '{species_class}':'{name}':'{code}'")

    # get a breed object relying on parameters
    qs = Breed.objects(species=species_class, name=name, code=code)

    modified = False

    if qs.count() == 1:
        breed = qs.get()
        logger.debug(f"Got {breed}")
        for alias in aliases:
            if alias not in breed.aliases:
                # track for update
                modified = True

                logger.info(f"Adding '{alias}' to '{breed}' aliases")
                breed.aliases.append(alias)

    elif qs.count() == 0:
        logger.debug("Create a new breed object")
        modified = True

        breed = Breed(
            species=species_class,
            name=name,
            code=code,
            aliases=aliases,
            n_individuals=0
        )

    else:
        # should never see this relying on collection unique keys
        raise SmarterDBException(
            f"Got {qs.count()} results for '{species_class}':'{name}': "
            f"'{code}'")

    if modified:
        logger.debug(f"Save '{breed}' to database")
        breed.save()

    return breed, modified


class Dataset(mongoengine.Document):
    """Describe a dataset instace with fields owned by data types"""

    file = mongoengine.StringField(required=True, unique=True)
    """The source dataset file"""

    uploader = mongoengine.StringField()
    """The partner which upload this dataset"""

    size_ = mongoengine.StringField(db_field="size")
    """The file size"""

    partner = mongoengine.StringField()
    """The partner which owns the dataset"""

    # HINT: should country, species and breeds be a list of items?
    country = mongoengine.StringField()
    """The country where the data come from. Could have many values"""

    species = mongoengine.StringField()
    """The species of the data. Could be 'Sheep' or 'Goat'"""

    breed = mongoengine.StringField()
    """The breed of the dataset. Could have many values"""

    n_of_individuals = mongoengine.IntField()
    """Number of individual in the dataset"""

    n_of_records = mongoengine.IntField()
    """Number of the record in the phenotype file"""

    trait = mongoengine.StringField()
    """Trait described in phenotype file"""

    gene_array = mongoengine.StringField()
    """The technology used to generate data specified by the partner"""

    # add type tag
    type_ = mongoengine.ListField(mongoengine.StringField(), db_field="type")
    """Dataset type. Need to be one from ``['genotypes', 'phenotypes]``
    and one from ``['background', 'foreground']``"""

    # file contents
    contents = mongoengine.ListField(mongoengine.StringField())
    """Dataset contents as a list"""

    # track the original chip_name with dataset
    chip_name = mongoengine.StringField()
    """The :py:class:`SupportedChip.name` attribute of the
    technology used"""

    doi = mongoengine.URLField()
    """The publication DOI of this dataset"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'dataset'
    }

    def __str__(self):
        return f"file={self.file}, uploader={self.uploader}"

    @property
    def working_dir(self) -> pathlib.PosixPath:
        """returns the locations of dataset working directory. Could exists
        or not

        Returns:
            pathlib.PosixPath: a subdirectory in /data/interim/
        """

        if not self.id:
            raise SmarterDBException(
                "Can't define working dir. Object need to be stored in "
                "database")

        return get_project_dir() / f"data/interim/{self.id}"

    @property
    def result_dir(self) -> pathlib.PosixPath:
        """returns the locations of dataset processed directory. Could exists
        or not

        Returns:
            pathlib.PosixPath: a subdirectory in /data/processed/
        """

        if not self.id:
            raise SmarterDBException(
                "Can't define result dir. Object need to be stored in "
                "database")

        return get_project_dir() / f"data/processed/{self.id}"


def getNextSequenceValue(
        sequence_name: str, mongodb: database.Database):
    """Read from :py:class:`Counter` collection and determine the next sequence
    number to be used for the SMARTER ID"""

    # this method is something similar to findAndModify,
    # update a document and after get the UPDATED document
    # https://docs.mongodb.com/manual/reference/method/db.collection.findAndModify/index.html#db.collection.findAndModify
    sequenceDocument = mongodb.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        return_document=ReturnDocument.AFTER
    )

    return sequenceDocument['sequence_value']


def getSmarterId(
        species_class: str,
        country: str,
        breed: str) -> str:
    """
    Generate a new SMARTER ID object using the internal counter collections

    Parameters
    ----------
    species_class : str
        The class of the species (should be 'Goat' or 'Sheep').
    country : str
        The country name of the sample.
    breed : str
        The breed name of the sample.

    Raises
    ------
    SmarterDBException
        Raised when passing a wrong species or no one.

    Returns
    -------
    str
        A new smarter_id.
    """

    # this should be the connection I made
    global SMARTERDB, SPECIES2CODE

    # species_class, country and breed shold be defined
    if not species_class or not country or not breed:
        raise SmarterDBException(
            "species, country and breed should be defined when calling "
            "getSmarterId"
        )

    # get species code
    if species_class not in SPECIES2CODE:
        raise SmarterDBException(
            "Species %s not managed by smarter" % (species_class))

    species_code = SPECIES2CODE[species_class]

    # get a country object
    if country.lower() == "unknown":
        country = UnknownCountry()
    else:
        country = countries.get(name=country)

    # get two letter code for country
    country_code = country.alpha_2

    # get breed code from database
    database = mongoengine.connection.get_db(alias=DB_ALIAS)
    breed_code = database.breeds.find_one(
        {"species": species_class, "name": breed})["code"]

    # derive sequence_name from species_class
    sequence_name = f"sample{species_class}"

    # get the sequence number and define smarter id
    sequence_id = getNextSequenceValue(
        sequence_name, database)

    # padding numbers
    sequence_id = str(sequence_id).zfill(9)

    smarter_id = f"{country_code}{species_code}-{breed_code}-{sequence_id}"

    return smarter_id


class SEX(bytes, Enum):
    """An enum object to manage Sample sex in the same way as plink does"""

    UNKNOWN = (0, "Unknown")
    MALE = (1, "Male")
    FEMALE = (2, "Female")

    def __new__(cls, value, label):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.label = label
        return obj

    def __str__(self):
        return self.label

    @classmethod
    def from_string(cls, value: str):
        """Get proper type relying on input string

        Args:
            value (str): required sex as string

        Returns:
            SEX: A sex instance (MALE, FEMALE, UNKNOWN)
        """

        if not isinstance(value, str):
            raise SmarterDBException("Provided value should be a 'str' type")

        value = value.upper()

        if value in ['M', 'MALE', "1"]:
            return cls.MALE

        elif value in ['F', 'FEMALE', "2"]:
            return cls.FEMALE

        else:
            logger.debug(
                f"Unmanaged sex '{value}': return '{cls.UNKNOWN}'")
            return cls.UNKNOWN


class Phenotype(mongoengine.DynamicEmbeddedDocument):
    """A class to deal with phenotypes. This is a dynamic document and not a
    generic DictField since there can be attributes which could be enforced to
    have certain values. All other attributes could be set without any
    assumptions
    """

    purpose = mongoengine.StringField()
    chest_girth = mongoengine.FloatField()
    height = mongoengine.FloatField()
    length = mongoengine.FloatField()

    def __str__(self):
        return f"{self.to_json()}"


class SAMPLETYPE(Enum):
    """A simple Enum object to define sample type (``background`` or
    ``foreground``)"""

    FOREGROUND = 'foreground'
    BACKGROUND = 'background'


class SampleSpecies(mongoengine.Document):
    """A generic class used to manage Goat or Sheep samples"""

    original_id = mongoengine.StringField(required=True)
    """The sample original ID in the source dataset"""

    smarter_id = mongoengine.StringField(required=True, unique=True)
    """A SMARTER unique and stable identifier"""

    country = mongoengine.StringField(required=True)
    """Where this samples comes from"""

    # generic species type (required to derive other stuff)
    species_class = None
    """A generic species (Sheep or Goat). Used to determine specific methods
    and to identify the proper data from the database"""

    breed = mongoengine.StringField(required=True)
    """The breed full name"""

    breed_code = mongoengine.StringField(min_length=2)
    """The breed code"""

    # this will be a original_id alias (a different sample name in original
    # data file)
    alias = mongoengine.StringField()
    """This is a sample alias, mainly the name used in the genotype file, which
    can be different from the name specified in the metadata file"""

    # required to search a sample relying only on original ID
    dataset = mongoengine.ReferenceField(
        Dataset,
        db_field="dataset_id",
        reverse_delete_rule=mongoengine.DENY
    )
    """The dataset where this sample come from"""

    # add type tag
    type_ = mongoengine.EnumField(SAMPLETYPE, db_field="type", required=True)
    """A :py:class:`SAMPLETYPE` instance (ie, ``background`` or ``foreground``
    """

    # track the original chip_name with sample
    chip_name = mongoengine.StringField()
    """The chip name used to define this sample"""

    # define enum types for sex
    sex = mongoengine.EnumField(SEX)
    """A :py:class:`SEX` instance. Store sex like plink does"""

    # GPS location
    # NOTE: X, Y where X is longitude, Y latitude
    locations = mongoengine.fields.MultiPointField(
        auto_index=True, default=None)
    """The sample GPS location as a Point (X, Y -> longitude, latitude). Mind
    that a location is specified in latitude and longitude coordinates.
    Specifying coordinates header in general is useful to avoid errors"""

    # additional (not modelled) metadata
    metadata = mongoengine.DictField(default=None)
    """Additional metadata (not managed via ORM)"""

    # for phenotypes
    phenotype = mongoengine.EmbeddedDocumentField(Phenotype, default=None)
    """A :py:class:`Phenotype` instance"""

    meta = {
        'abstract': True,
        'indexes': [
            [("locations", "2dsphere")]
        ]
    }

    def save(self, *args, **kwargs):
        """Custom save method. Deal with smarter_id before save"""

        if not self.smarter_id:
            logger.debug(f"Determining smarter id for {self.original_id}")

            # even is species, country and breed are required fields for
            # SampleSpecies document, their value will not be evaluated until
            # super().save() is called. I can't call it before determining
            # a smarter_id
            self.smarter_id = getSmarterId(
                self.species_class,
                self.country,
                self.breed)

        # default save method
        super(SampleSpecies, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.smarter_id} ({self.breed})"


class SampleSheep(SampleSpecies):
    """A class specific for Sheep samples"""

    species = mongoengine.StringField(required=True, default="Ovis aries")
    """The species name. Could be something different from ``Ovis aries``"""

    # generic species type (required to derive other stuff)
    species_class = "Sheep"
    """The generic specie class"""

    # try to model relationship between samples
    father_id = mongoengine.LazyReferenceField(
        'SampleSheep',
        passthrough=True,
        reverse_delete_rule=mongoengine.NULLIFY
    )
    """The father (SIRE) of this animal. Is a reference to another SampleSheep
    instance"""

    mother_id = mongoengine.LazyReferenceField(
        'SampleSheep',
        passthrough=True,
        reverse_delete_rule=mongoengine.NULLIFY
    )
    """The mother (DAM) of this animal. Is a reference to another SampleSheep
    instance"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'sampleSheep'
    }


class SampleGoat(SampleSpecies):
    """A class specific for Goat samples"""

    species = mongoengine.StringField(required=True, default="Capra hircus")
    """The species name. Could be something different from ``Capra hircus``"""

    # generic species type (required to derive other stuff)
    species_class = "Goat"
    """The generic specie class"""

    # try to model relationship between samples
    father_id = mongoengine.LazyReferenceField(
        'SampleGoat',
        passthrough=True,
        reverse_delete_rule=mongoengine.NULLIFY
    )
    """The father (SIRE) of this animal. Is a reference to another SampleGoat
    instance"""

    mother_id = mongoengine.LazyReferenceField(
        'SampleGoat',
        passthrough=True,
        reverse_delete_rule=mongoengine.NULLIFY
    )
    """The mother (DAM) of this animal. Is a reference to another SampleGoat
    instance"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'sampleGoat'
    }


def get_or_create_sample(
        SampleSpecies: Union[SampleGoat, SampleSheep],
        original_id: str,
        dataset: Dataset,
        type_: str,
        breed: Breed,
        country: str,
        species: str = None,
        chip_name: str = None,
        sex: SEX = None,
        alias: str = None) -> list[Union[SampleGoat, SampleSheep], bool]:
    """
    Get or create a sample providing attributes (search for original_id in
    provided dataset

    Parameters
    ----------
    SampleSpecies : Union[SampleGoat, SampleSheep]
        the class required for insert/update.
    original_id : str
        the original_id in the dataset.
    dataset : Dataset
        the dataset instance used to register sample.
    type_ : str
        sample type. "background" or "foreground" are the only values accepted
    breed : Breed
        a :py:class:`Breed` instance.
    country : str
        the country where the sample comes from.
    species : str, optional
        The sample species. If None, the default `species_class` attribute
        will be used
    chip_name : str, optional
        the chip name. The default is None.
    sex : SEX, optional
        A :py:class:`SEX` instance. The default is None.
    alias : str, optional
         an original_id alias. Could be the name used in the genotype file,
         which could be different from the original_id. The default is None.

    Raises
    ------
    SmarterDBException
        Raised multiple samples are returned (should never happen).

    Returns
    -------
    Union[SampleGoat, SampleSheep]
        a SampleSpecies instance.
    created : bool
        True is sample is created.
    """

    created = False

    # coerce alias as integer (if any)
    if alias:
        alias = str(alias)

    # search for sample in database
    qs = SampleSpecies.objects(
        original_id=original_id,
        breed_code=breed.code,
        dataset=dataset,
        alias=alias)

    if qs.count() == 1:
        logger.debug(f"Sample '{original_id}', alias: '{alias}' "
                     "found in database")
        sample = qs.get()

    elif qs.count() == 0:
        # insert sample into database
        logger.info(f"Registering sample '{original_id}' in database")
        sample = SampleSpecies(
            original_id=original_id,
            country=country,
            species=species,
            breed=breed.name,
            breed_code=breed.code,
            dataset=dataset,
            type_=type_,
            chip_name=chip_name,
            sex=sex,
            alias=alias
        )
        sample.save()

        logger.debug(
            f"Created sample '{sample}' with original_id: '{original_id}', "
            f"country: '{country}', species: '{species}', breed: "
            f"'{breed.name}', breed_code: '{breed.code}', dataset: "
            f"'{dataset}', type: '{type_}', chip_name: '{chip_name}', "
            f"sex: '{sex}', alias: '{alias}'"
        )

        # incrementing breed n_individuals counter
        breed.n_individuals += 1
        breed.save()

        created = True

    else:
        raise SmarterDBException(
            f"Got {qs.count()} results for '{original_id}'")

    return sample, created


def get_sample_type(dataset: Dataset):
    """
    test if foreground or background dataset

    Args:
        dataset (Dataset): the dataset instance used to register sample

    Returns:
        str: sample type ("background" or "foreground")
    """

    type_ = None

    for sampletype in SAMPLETYPE:
        if sampletype.value in dataset.type_:
            logger.debug(
                f"Found {sampletype.value} in {dataset.type_}")
            type_ = sampletype.value
            break

    return type_


class Consequence(mongoengine.EmbeddedDocument):
    """A class to manage SNP consequences. Not yet implemented"""
    pass


class Location(mongoengine.EmbeddedDocument):
    """A class to deal with a SNP location (ie position in an assembly for
    a certain chip or data source)"""

    ss_id = mongoengine.StringField()
    """The SNP subission ID"""

    version = mongoengine.StringField(required=True)
    """The assembly version where this SNP is placed"""

    chrom = mongoengine.StringField(required=True)
    """The chromosome where this SNP is located"""

    position = mongoengine.IntField(required=True)
    """The SNP position"""

    alleles = mongoengine.StringField()
    """The dbSNP alleles of such SNP"""

    illumina = mongoengine.StringField(required=True)
    """The SNP code read as it is from illumina data"""

    illumina_forward = mongoengine.StringField()
    """The SNP code in illumina forward coding"""

    illumina_strand = mongoengine.StringField()
    """The probe orientation in alignment"""

    affymetrix_ab = mongoengine.StringField()
    """The SNP code read as it is from affymetrix data"""

    strand = mongoengine.StringField()
    """The strand orientation in aligment"""

    imported_from = mongoengine.StringField(required=True)
    """The source of the SNP data"""

    # this could be the manifactured date or the last updated
    date = mongoengine.DateTimeField()
    """Track manifactured date or when this data was last updated"""

    consequences = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Consequence), default=None)
    """A list of SNP consequences (not yet implemented)"""

    def __init__(self, *args, **kwargs):
        illumina_top = None

        # remove illumina top from arguments
        if 'illumina_top' in kwargs:
            illumina_top = kwargs.pop('illumina_top')

        # initialize base object
        super(Location, self).__init__(*args, **kwargs)

        # fix illumina top if necessary
        if illumina_top:
            self.illumina_top = illumina_top

    @property
    def illumina_top(self):
        """Return genotype in illumina top format"""

        if self.illumina_strand in ['BOT', 'bottom']:
            return complement(self.illumina)

        elif (not self.illumina_strand or
              self.illumina_strand in ['TOP', 'top']):
            return self.illumina

        else:
            raise SmarterDBException(
                f"{self.illumina_strand} not managed")

    @illumina_top.setter
    def illumina_top(self, genotype: str):
        if (not self.illumina_strand or
                self.illumina_strand in ['TOP', 'top']):
            self.illumina = genotype

        elif self.illumina_strand in ['BOT', 'bottom']:
            self.illumina = complement(genotype)

        else:
            raise SmarterDBException(
                f"{self.illumina_strand} not managed")

    def __str__(self):
        return (
            f"({self.imported_from}:{self.version}) "
            f"{self.chrom}:{self.position} [{self.illumina_top}]"
        )

    def __eq__(self, other):
        if super().__eq__(other):
            return True

        else:
            # check by positions
            for attribute in ["chrom", "position"]:
                if getattr(self, attribute) != getattr(other, attribute):
                    return False

            # check genotype equality
            if self.illumina_top != other.illumina_top:
                return False

            return True

    def __check_coding(self, genotype: list, coding: str, missing: str):
        """Internal method to check genotype coding"""

        if not getattr(self, coding):
            raise SmarterDBException(
                f"There's no information for '{coding}' in '{self}'")

        # get illumina data as an array
        data = getattr(self, coding).split("/")

        for allele in genotype:
            # mind to missing values. If missing can't be equal to illumina_top
            if allele in missing:
                continue

            if allele not in data:
                return False

        return True

    def is_top(self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with illumina TOP coding

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            bool: True if in top coding
        """

        return self.__check_coding(genotype, "illumina_top", missing)

    def is_forward(self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with illumina FORWARD coding

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            bool: True if in forward coding
        """

        return self.__check_coding(genotype, "illumina_forward", missing)

    def is_ab(self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with illumina AB coding

        Args:
            genotype (list): a list of two alleles (ex ['A','B'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            bool: True if in AB coding
        """

        for allele in genotype:
            # mind to missing valies
            if allele not in ["A", "B"] + missing:
                return False

        return True

    def is_affymetrix(
            self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with affymetrix coding

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            bool: True if in affymetrix AB coding
        """

        return self.__check_coding(genotype, "affymetrix_ab", missing)

    def is_illumina(
            self, genotype: list, missing: list = ["0", "-"]) -> bool:
        """Return True if genotype is compatible with illumina coding
        (as it's recorded in manifest)

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            bool: True if in affymetrix AB coding
        """

        return self.__check_coding(genotype, "illumina", missing)

    def forward2top(self, genotype: list, missing: list = ["0", "-"]) -> list:
        """Convert an illumina forward SNP in a illumina top snp

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            list: The genotype in top format
        """

        # get illumina data as an array
        forward = self.illumina_forward.split("/")
        top = self.illumina_top.split("/")

        result = []

        for allele in genotype:
            # mind to missing values
            if allele in missing:
                result.append("0")

            elif allele not in forward:
                raise SmarterDBException(
                    f"{genotype} is not in forward coding")

            else:
                result.append(top[forward.index(allele)])

        return result

    def top2forward(self, genotype: list, missing: list = ["0", "-"]) -> list:
        """Convert an illumina top SNP in a illumina forward snp

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            list: The genotype in forward format
        """

        # get illumina data as an array
        forward = self.illumina_forward.split("/")
        top = self.illumina_top.split("/")

        result = []

        for allele in genotype:
            # mind to missing values
            if allele in missing:
                result.append("0")

            elif allele not in top:
                raise SmarterDBException(
                    f"{genotype} is not in top coding")

            else:
                result.append(forward[top.index(allele)])

        return result

    def ab2top(self, genotype: list, missing: list = ["0", "-"]) -> list:
        """Convert an illumina ab SNP in a illumina top snp

        Args:
            genotype (list): a list of two alleles (ex ['A','B'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            list: The genotype in top format
        """

        # get illumina data as a dict
        top = self.illumina_top.split("/")
        top = {"A": top[0], "B": top[1]}

        result = []

        for allele in genotype:
            # mind to missing values
            if allele in missing:
                result.append("0")

            elif allele not in ["A", "B"]:
                raise SmarterDBException(
                    f"{genotype} is not in ab coding")

            else:
                result.append(top[allele])

        return result

    def affy2top(self, genotype: list, missing: list = ["0", "-"]) -> list:
        """Convert an affymetrix SNP in a illumina top snp

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            list: The genotype in top format
        """

        # get illumina data as an array
        affymetrix = self.affymetrix_ab.split("/")
        top = self.illumina_top.split("/")

        result = []

        for allele in genotype:
            # mind to missing values
            if allele in missing:
                result.append("0")

            elif allele not in affymetrix:
                raise SmarterDBException(
                    f"{genotype} is not in affymetrix coding")

            else:
                result.append(top[affymetrix.index(allele)])

        return result

    def illumina2top(self, genotype: list, missing: list = ["0", "-"]) -> list:
        """Convert an illumina SNP in a illumina top snp

        Args:
            genotype (list): a list of two alleles (ex ['A','C'])
            missing (list): a list of missing allele strings (def ["0", "-"])

        Returns:
            list: The genotype in top format
        """

        # get illumina data as an array
        illumina = self.illumina.split("/")
        top = self.illumina_top.split("/")

        result = []

        for allele in genotype:
            # mind to missing values
            if allele in missing:
                result.append("0")

            elif allele not in illumina:
                raise SmarterDBException(
                    f"{genotype} is not in illumina coding")

            else:
                result.append(top[illumina.index(allele)])

        return result


class Probeset(mongoengine.EmbeddedDocument):
    """A class to deal with different affymetrix probesets"""

    chip_name = mongoengine.StringField(required=True)
    """the chip name where this affymetrix probeset comes from"""

    # more probe could be assigned to the same SNP
    probeset_id = mongoengine.ListField(mongoengine.StringField())
    """A list probeset assigned to the same SNP"""

    def __str__(self):
        return (
            f"{self.chip_name}: {self.probeset_id}"
        )


class VariantSpecies(mongoengine.Document):
    """Generic class to deal with Variant (SNP) objects"""

    rs_id = mongoengine.ListField(mongoengine.StringField(), default=None)
    """The SNP rsID"""

    chip_name = mongoengine.ListField(mongoengine.StringField())
    """The chip names where this SNP could be found"""

    name = mongoengine.StringField(unique=True)
    """The name of the SNPs. Could be illumina name or affyemtrix name"""

    # sequence should model both illumina or affymetrix sequences
    sequence = mongoengine.DictField()
    """A dictionary where keys are chip_name, and values are their probe
    sequences"""

    # illumina top variant at variant level
    illumina_top = mongoengine.StringField(required=True)
    """Illumina TOP variant (which is the same indipendently by locations)"""

    locations = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Location))
    """A list of :py:class:`Location` objects"""

    # HINT: should sender be a Location attribute?
    sender = mongoengine.StringField()
    """Who provide this SNP probe"""

    # Affymetryx specific fields
    probesets = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(Probeset), default=None)
    """A list of :py:class:`Probeset` objects"""

    affy_snp_id = mongoengine.StringField()
    """The affymetrix SNP id"""

    cust_id = mongoengine.StringField()
    """The affymetrix customer id (which is the illumina name)"""

    # abstract class with custom indexes
    # TODO: need a index for position (chrom, position, version)
    meta = {
        'abstract': True,
        'indexes': [
            {
                'fields': [
                    "locations.chrom",
                    "locations.position"
                ],
            },
            {
                'fields': ["affy_snp_id"],
                'partialFilterExpression': {
                    "affy_snp_id": {
                        "$exists": True
                    }
                }
            },
            "probesets.probeset_id",
            'rs_id',
        ]
    }

    def __str__(self):
        if not self.name and self.affy_snp_id:
            return (
                f"affy_snp_id='{self.affy_snp_id}', rs_id='{self.rs_id}', "
                f"illumina_top='{self.illumina_top}'")

        return (
            f"name='{self.name}', rs_id='{self.rs_id}', "
            f"illumina_top='{self.illumina_top}'")

    def save(self, *args, **kwargs):
        """Custom save method. Deal with variant name before save"""

        if not self.name and self.affy_snp_id:
            logger.debug(f"Set variant name to {self.affy_snp_id}")
            self.name = self.affy_snp_id

        # default save method
        super(VariantSpecies, self).save(*args, **kwargs)

    def get_location_index(self, version: str, imported_from='SNPchiMp v.3'):
        """Returns location index for assembly version and imported source

        Args:
            version (str): assembly version (ex: 'Oar_v3.1')
            imported_from (str): coordinates source (ex: 'SNPchiMp v.3')

        Returns:
            int: the index of the location requested
        """

        for index, location in enumerate(self.locations):
            if (location.version == version and
                    location.imported_from == imported_from):
                return index

        raise SmarterDBException(
                f"Location '{version}' '{imported_from}' is not in locations"
        )

    def get_location(self, version: str, imported_from='SNPchiMp v.3'):
        """Returns location for assembly version and imported source

        Args:
            version (str): assembly version (ex: 'Oar_v3.1')
            imported_from (str): coordinates source (ex: 'SNPchiMp v.3')

        Returns:
            Location: the genomic coordinates
        """

        def custom_filter(location: Location):
            if (location.version == version and
                    location.imported_from == imported_from):
                return True

            return False

        locations = list(filter(custom_filter, self.locations))

        if len(locations) != 1:
            raise SmarterDBException(
                "Couldn't determine a unique location for "
                f"'{self.name}' '{version}' '{imported_from}'")

        return locations[0]


class VariantSheep(VariantSpecies):
    """A class to deal with Sheep variations (SNP)"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'variantSheep'
    }


class VariantGoat(VariantSpecies):
    """A class to deal with Goat variations (SNP)"""

    meta = {
        'db_alias': DB_ALIAS,
        'collection': 'variantGoat'
    }
