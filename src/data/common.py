#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 15:13:32 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Common stuff for smarter scripts
"""

import logging

from typing import Union
from pathlib import Path
from collections import namedtuple

from mongoengine.queryset import QuerySet

import pandas as pd

from src.features.smarterdb import (
    Dataset, VariantGoat, VariantSheep, SampleSheep, SampleGoat, Location,
    Probeset, SmarterDBException, SEX)

# Get an instance of a logger
logger = logging.getLogger(__name__)

# defining here supported assemblies and version info
AssemblyConf = namedtuple('AssemblyConf', ['version', 'imported_from'])

WORKING_ASSEMBLIES = {
    'OAR3': AssemblyConf('Oar_v3.1', 'SNPchiMp v.3'),
    'OAR4': AssemblyConf('Oar_v4.0', 'SNPchiMp v.3'),
    'ARS1': AssemblyConf('ARS1', 'manifest'),
    'CHI1': AssemblyConf('CHI1.0', 'SNPchiMp v.3')
}

PLINK_SPECIES_OPT = {
    # got this one from documentation + allow-no-sex, since I have
    # phenotypes with ambigous sex
    'Sheep': ['--chr-set', '26', 'no-xy', 'no-mt', '--allow-no-sex'],
    # this let to model 29 chromosome, X, Y, MT and contigs
    'Goat': ['--chr-set', '29', '--allow-extra-chr']
}


def fetch_and_check_dataset(
        archive: str, contents: list[str]) -> [Dataset, list[Path]]:
    """Common operations on dataset: fetch a dataset by file (submitted
    archive), check that working dir exists and required file contents is
    in dataset. Test and get full path of required files

    Args:
        archive (str): the dataset archive (file)
        contents (list): a list of files which beed to be defined in dataset

    Returns:
        Dataset: a dataset instance
        list[Path]: a list of Path of required files
    """

    # get the dataset object
    dataset = Dataset.objects(file=archive).get()

    logger.debug(f"Found {dataset}")

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        raise FileNotFoundError(
            f"Could find dataset directory '{working_dir}'")

    # check files are in dataset
    not_found = []
    contents_path = []

    for item in contents:
        if item not in dataset.contents:
            logger.error(f"Couldn't find '{item}' in dataset: '{dataset}'")
            not_found.append(item)
            continue

        item_path = working_dir / item

        if not item_path.exists():
            logger.error(
                f"Couldn't find '{item_path}' in dir: '{working_dir}'")
            not_found.append(item)
            continue

        contents_path.append(item_path)

    if len(not_found) > 0:
        raise FileNotFoundError(
            f"Couldn't find '{not_found}'")

    return dataset, contents_path


def deal_with_datasets(
        src_dataset: str,
        dst_dataset: str,
        datafile: str) -> [Dataset, Dataset, Path]:
    """Check source and destination dataset with its content"""

    # custom method to check a dataset and ensure that needed stuff exists
    src_dataset, [datapath] = fetch_and_check_dataset(
        archive=src_dataset,
        contents=[datafile]
    )

    if not dst_dataset:
        # destination is the same of origin, if not provided
        dst_dataset = src_dataset

    else:
        # this will be the dataset used to define samples
        dst_dataset, _ = fetch_and_check_dataset(
            archive=dst_dataset,
            contents=[]
        )

    return src_dataset, dst_dataset, datapath


def get_variant_species(species: str) -> Union[VariantSheep, VariantGoat]:
    """Get a species name in input. It return the proper VariantSpecies class

    Args:
        species (str): the species name

    Returns:
        Union[VariantSheep, VariantGoat]: a VariantSpecies class
    """

    # fix input parameters
    species = species.capitalize()

    if species == 'Sheep':
        VariantSpecie = VariantSheep

    elif species == 'Goat':
        VariantSpecie = VariantGoat

    else:
        raise NotImplementedError(f"'{species}' import not yet implemented")

    return VariantSpecie


def get_sample_species(species: str) -> Union[SampleSheep, SampleGoat]:
    """Get a species name in input. It return the proper SampleSpecies class

    Args:
        species (str): the species name

    Returns:
        Union[SampleSheep, SampleGoat]: a SampleSpecies class
    """

    # fix input parameters
    species = species.capitalize()

    # mind dataset species
    if species == 'Sheep':
        SampleSpecie = SampleSheep

    elif species == 'Goat':
        SampleSpecie = SampleGoat

    else:
        raise NotImplementedError(
            f"'{species}' import not yet implemented")

    return SampleSpecie


def pandas_open(datapath: Path, **kwargs) -> pd.DataFrame:
    """Open an excel or csv file with pandas and returns a dataframe

    Args:
        datapath (Path): the path of the file
        kwargs (dict): additional pandas options

    Returns:
        pd.DataFrame: file content as a pandas dataframe
    """

    data = None

    if datapath.suffix in ['.xls', '.xlsx']:
        with open(datapath, "rb") as handle:
            data = pd.read_excel(handle, **kwargs)

    elif datapath.suffix == '.csv':
        with open(datapath, "r") as handle:
            # set separator to None force pandas to use csv.Sniffer
            data = pd.read_csv(handle, sep=None, engine='python', **kwargs)

    else:
        raise Exception(
            f"'{datapath.suffix}' file type not managed"
        )

    return data


def new_variant(
        variant: Union[VariantSheep, VariantGoat],
        location: Location):

    variant.locations.append(location)

    # set the illumina_top attribute relying on the first location
    variant.illumina_top = location.illumina_top

    logger.debug(f"adding {variant} to database")

    variant.save()


def update_variant(
        qs: QuerySet,
        variant: Union[VariantSheep, VariantGoat],
        location: Location) -> bool:
    """Update an existing variant (if necessary)"""

    record = qs.get()
    logger.debug(f"found {record} in database")

    update_record = False

    # check that the snp I want to update has the same illumina_top
    # allele with the new location: if not no update!
    if record.illumina_top != location.illumina_top:
        logger.error(
            f"illumina_top alleles between variant and new location don't "
            f"match: {record.illumina_top} <> {location.illumina_top}")
        logger.warning(f"ignoring {variant}")
        return update_record

    # check chip_name in variant list
    record, updated = update_chip_name(variant, record)

    if updated:
        update_record = True

    # update sequence record
    record, updated = update_sequence(variant, record)

    if updated:
        update_record = True

    # test for rs_id:
    record, updated = update_rs_id(variant, record)

    if updated:
        update_record = True

    # update affymetrix record (if any)
    record, updated = update_affymetrix_record(variant, record)

    if updated:
        update_record = True

    # I chose to not update other values, I suppose they be the same
    # However check for locations
    record, updated = update_location(location, record)

    if updated:
        update_record = True

    if update_record:
        record.save()

    return update_record


def update_chip_name(
        variant: Union[VariantSheep, VariantGoat],
        record: Union[VariantSheep, VariantGoat]
        ) -> [Union[VariantSheep, VariantGoat], bool]:
    variant_set = set(variant.chip_name)
    record_set = set(record.chip_name)

    updated = False

    # get new items as a difference of two sets
    new_chips = variant_set - record_set

    if len(new_chips) > 0:
        # this will append the resulting set as a list
        record.chip_name += list(new_chips)
        updated = True

    return record, updated


def update_sequence(
        variant: Union[VariantSheep, VariantGoat],
        record: Union[VariantSheep, VariantGoat]
        ) -> [Union[VariantSheep, VariantGoat], bool]:

    updated = False

    if variant.sequence and variant.sequence != record.sequence:
        record.sequence.update(variant.sequence)
        updated = True

    return record, updated


def update_probesets(
        variant_attr: list[Probeset],
        record_attr: list[Probeset]
        ) -> bool:
    """Update probeset relying on object references"""

    updated = False

    logger.debug(f"Got variant: {variant_attr} and record: {record_attr}")

    # get the variant probeset
    variant_probeset = variant_attr[0]

    # now, try to get the variant probesed for the same chip
    record_probesets = list(
        filter(
            lambda probeset: probeset.chip_name == variant_probeset.chip_name,
            record_attr)
    )

    if not record_probesets:
        # I don't have this probeset_id for this chip
        record_attr.append(variant_probeset)
        updated = True

    else:
        # get the first item
        record_probeset = record_probesets[0]
        record_set = set(record_probeset.probeset_id)
        variant_set = set(variant_probeset.probeset_id)

        # get new items as a difference of two sets
        new_probeset_ids = variant_set - record_set

        if len(new_probeset_ids) > 0:
            # this will append the resulting set as a list
            record_probeset.probeset_id += list(new_probeset_ids)
            updated = True

    return updated


def update_affymetrix_record(
        variant: Union[VariantSheep, VariantGoat],
        record: Union[VariantSheep, VariantGoat]
        ) -> [Union[VariantSheep, VariantGoat], bool]:

    updated = False

    for key in ['probesets', 'affy_snp_id', 'cust_id']:
        variant_attr = getattr(variant, key)
        record_attr = getattr(record, key)

        if key == 'probesets' and variant_attr:
            if record_attr:
                # this will make an update relying on object references
                updated = update_probesets(variant_attr, record_attr)
            else:
                # this is when I add a probeset for an Illumina SNP
                setattr(record, key, variant_attr)
                updated = True

        elif key == 'cust_id':
            # only update cust_id if different from illumina name and
            # if necessary
            if variant_attr and variant_attr not in [record.name, record_attr]:
                if record_attr:
                    logger.warning(
                        f"Updating {key}: '{variant_attr}' with "
                        f"'{record_attr}'")

                setattr(record, key, variant_attr)
                updated = True

        elif key == 'affy_snp_id':
            if variant_attr and variant_attr != record_attr:
                if record_attr:
                    raise SmarterDBException(
                        f"Error with {key}: '{variant_attr}' and "
                        f"'{record_attr}': 'affy_snp_id' already defined!")

                setattr(record, key, variant_attr)
                updated = True

    return record, updated


def update_location(
        location: Location,
        variant: Union[VariantSheep, VariantGoat],
        force_update: bool = False
        ) -> [Union[VariantSheep, VariantGoat], bool]:
    """
    Check provided Location with variant Locations: append new object or
    update a Location object if more recent than the data stored in database

    Parameters
    ----------
    location : Location
        The location to test against the database.
    variant : Union[VariantSheep, VariantGoat]
        The variant to test.
    force_update : bool, optional
        Force location update. The default is False.

    Returns
    -------
    [Union[VariantSheep, VariantGoat], bool]
        A list with the updated VariantSpecie object and a boolean value
        which is True if the location was updated
    """

    updated = False

    if location.date:
        # make location.date offset-naive
        # https://stackoverflow.com/a/796019
        location.date = location.date.replace(tzinfo=None)

    # get the old location as index
    try:
        index = variant.get_location_index(
            version=location.version, imported_from=location.imported_from)

        if force_update:
            # update location
            logger.warning(
                f"Force update for '{variant}' location")
            variant.locations[index] = location
            updated = True

            return variant, updated

        # ok get the old location and check with the new one
        old_location = variant.locations[index]

        if old_location == location:
            logger.debug("Locations match")

        # upgrade locations relying dates
        else:
            logger.warning(
                f"Locations differ for '{variant.name}': {location} <> "
                f"{old_location}"
            )

            # check if values are defined
            if old_location.date and location.date:
                if old_location.date < location.date:
                    # update location
                    logger.warning(
                        f"Replacing location for '{variant}' since is newer")
                    variant.locations[index] = location
                    updated = True

                else:
                    logger.debug(
                        f"New location is not more recent than the old "
                        f"({location.date.date()}"
                        f" <> {old_location.date.date()}), ignoring location")

            else:
                logger.debug("Skip location comparison: dates not set")

    except SmarterDBException as exc:
        # if a index does not exist, then insert feature without warnings
        logger.debug(exc)

        # if I'm impotring Affymetrix data, I could have a variant but not
        # a location to check. So add a location to variant
        logger.debug(f"Append location {location} to variant {variant}")
        variant.locations.append(location)
        updated = True

    return variant, updated


def update_rs_id(
        variant: Union[VariantSheep, VariantGoat],
        record: Union[VariantSheep, VariantGoat]
        ) -> [Union[VariantSheep, VariantGoat], bool]:

    updated = False

    if variant.rs_id:
        if not record.rs_id:
            logger.debug(f"Setting '{variant.rs_id}' to '{record}'")
            record.rs_id = variant.rs_id
            updated = True

        elif variant.rs_id[0] not in record.rs_id:
            logger.debug(f"Appending '{variant.rs_id[0]}' to '{record}'")
            record.rs_id.append(variant.rs_id[0])
            updated = True

        else:
            logger.debug(f"Ignoring '{variant.rs_id[0]}: ({record})'")

    return record, updated


def deal_with_sex_and_alias(
        sex_column: str, alias_column: str, row: pd.Series):
    """
    Deal with sex and alias parameters

    Parameters
    ----------
    sex_column : str
        The sex column label.
    alias_column : str
        The alias column label.
    row : Series
        A row of metadata file.

    Returns
    -------
    sex : SEX
        A SEX instance.
    alias : str
        The alias read from metadata table could be None.

    """

    # Have I sex? search for a sex column if provided
    sex = None

    if sex_column:
        sex = str(row.get(sex_column)).strip()
        sex = SEX.from_string(sex)

        # drop sex column if unknown
        if sex == SEX.UNKNOWN:
            sex = None

    alias = None

    if alias_column:
        value = row.get(alias_column)

        if pd.notnull(value) and pd.notna(value):
            alias = value

    return sex, alias
