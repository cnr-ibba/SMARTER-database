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

import pandas as pd

from src.features.smarterdb import Dataset, VariantGoat, VariantSheep

# Get an instance of a logger
logger = logging.getLogger(__name__)

# defining here supported assemblies and version info
AssemblyConf = namedtuple('AssemblyConf', ['version', 'imported_from'])

WORKING_ASSEMBLIES = {
    'OAR3': AssemblyConf('Oar_v3.1', 'SNPchiMp v.3'),
    'ARS1': AssemblyConf('ARS1', 'manifest'),
    'CHI1': AssemblyConf('CHI1.0', 'SNPchiMp v.3')
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


def pandas_open(datapath: Path) -> pd.DataFrame:
    """Open an excel or csv file with pandas and returns a dataframe

    Args:
        datapath (Path): the path of the file

    Returns:
        pd.DataFrame: file content as a pandas dataframe
    """

    data = None

    if datapath.suffix in ['.xls', '.xlsx']:
        with open(datapath, "rb") as handle:
            data = pd.read_excel(handle)

    elif datapath.suffix == '.csv':
        with open(datapath, "r") as handle:
            # set separator to None force pandas to use csv.Sniffer
            data = pd.read_csv(handle, sep=None, engine='python')

    else:
        raise Exception(
            f"'{datapath.suffix}' file type not managed"
        )

    return data
