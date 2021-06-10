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

from mongoengine.errors import NotUniqueError
from mongoengine.queryset import QuerySet

import pandas as pd

from src.features.smarterdb import (
    Dataset, VariantGoat, VariantSheep, SampleSheep, SampleGoat, Location)

# Get an instance of a logger
logger = logging.getLogger(__name__)

# defining here supported assemblies and version info
AssemblyConf = namedtuple('AssemblyConf', ['version', 'imported_from'])

WORKING_ASSEMBLIES = {
    'OAR3': AssemblyConf('Oar_v3.1', 'SNPchiMp v.3'),
    'ARS1': AssemblyConf('ARS1', 'manifest'),
    'CHI1': AssemblyConf('CHI1.0', 'SNPchiMp v.3')
}

PLINK_SPECIES_OPT = {
    # got this one from documentation
    'Sheep': ['--chr-set', '26', 'no-xy', 'no-mt'],
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

    logger.info(f"adding {variant} to database")

    try:
        variant.save()

    except NotUniqueError as e:
        logger.error(
            f"Cannot insert {variant}, reason: {e}")


def update_variant(
        qs: QuerySet,
        variant: Union[VariantSheep, VariantGoat],
        location: Location):
    """Update an existing variant (if necessary)"""

    record = qs.get()
    logger.debug(f"found {record} in database")

    # check chip_name in variant list
    record = update_chip_name(variant, record)

    # I chose to not update other values, I suppose they be the same
    # However check for locations
    check_location(location, record)


def update_chip_name(variant, record):
    variant_set = set(variant.chip_name)
    record_set = set(record.chip_name)

    # get new items as a difference of two sets
    new_chips = variant_set - record_set

    if len(new_chips) > 0:
        # this will append the resulting set as a list
        record.chip_name += list(new_chips)
        record.save()

    return record


def check_location(location, variant):
    # get the old location as index
    index = variant.get_location_index(
        version=location.version, imported_from=location.imported_from)

    # ok get the old location and check with the new one
    if variant.locations[index] == location:
        logger.debug("Locations match")

    # HINT: should I update location?
    else:
        logger.warning(
            f"Locations differ: {location} <> {variant.locations[index]}")
