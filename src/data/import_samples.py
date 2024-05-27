#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  4 15:16:09 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

First attempt to create samples BEFORE reading genotype file. This is necessary
if we have breeds in different countries, since we can't read country from
breed aliases relying only on FID. Moreover this could manage also the
relationship problems (in order to have already all samples into database when
processing genotypes)
"""

import click
import logging
import functools

from pathlib import Path
from click_option_group import (
    optgroup, RequiredMutuallyExclusiveOptionGroup,
    MutuallyExclusiveOptionGroup)
from mongoengine.errors import DoesNotExist

from pandas.core.series import Series

from src.data.common import (
    deal_with_datasets, pandas_open, get_sample_species,
    deal_with_sex_and_alias)
from src.features.smarterdb import (
    global_connection, Breed, get_or_create_sample, get_sample_type,
    SmarterDBException)
from src.features.utils import UnknownCountry, countries

logger = logging.getLogger(__name__)


@functools.lru_cache
def find_country(country: str):
    """Do a fuzzy search with pycountry. Returns a pycountry object

    Args:
        country (str): the fuzzy country name

    Returns:
        pycountry.db.Country: the found country name
    """
    # mind underscore in country names: pycountry can't deal with them
    country = country.replace("_", " ")

    if country.lower() == "unknown":
        return UnknownCountry()

    # transform country string with pycountry
    fuzzy = countries.search_fuzzy(country)[0]

    logger.info(f"Found {fuzzy} for {country}")

    return fuzzy


def deal_with_breeds(
        code: str, code_column: str, dst_dataset: str, row: Series):
    """
    Determine breeds and code for each sample in dataset or apply the same
    stuff to each samples

    Parameters
    ----------
    code : str
        Search for a :py:class:`Breed` object using this code and dataset
    code_column : str
        The column label to be searched in dataframe.
    dst_dataset : Dataset
        The destination dataset.
    row : Series
        A row of metadata file.

    Returns
    -------
    breed : Breed
        A breed instance.
    code : str
        A breed code to be applied to sample.
    """

    # assign code from parameter or from datasource column
    # code_column has a default value. Check for provided code first
    if code:
        # get breed from database
        breed = Breed.objects(
            code=code,
            species=dst_dataset.species
        ).get()

    else:
        code = str(row.get(code_column))

        logger.debug(f"search for fid: {code}, dataset: {dst_dataset}")

        # get breed from database
        try:
            breed = Breed.objects(
                aliases__match={'fid': code, 'dataset': dst_dataset}).get()

        except DoesNotExist as exc:
            logger.debug(exc)
            raise SmarterDBException(
                f"Couldn't find fid: {code}, dataset: {dst_dataset}")

    logger.debug(f"found breed '{breed}'")

    return breed, code


def deal_with_countries(country: str, country_column: str, row: Series):
    """
    Search for countries relying on dataset or by input value

    Parameters
    ----------
    country_all : str
        Apply this country to sample.
    country_column : str
        The column label to be searched in dataframe.
    row : Series
        A row of metadata file.

    Returns
    -------
    str
        A country to be applied to the sample.
    """

    logger.debug(f"Got: {country}, {country_column}")

    # assign country from datasource column if specified
    # country_column has a default value. Check for provided country first
    if not country:
        country = row.get(country_column)

    # process a country by doing a fuzzy search
    # HINT: this function caches results relying arguments using lru_cache
    # see find country implementation for more informations
    return find_country(country)


@click.command()
@click.option(
    '--src_dataset', type=str, required=True,
    help="The raw dataset file name (zip archive) in which search datafile"
)
@click.option(
    '--dst_dataset', type=str, required=False,
    help=("The raw dataset file name (zip archive) in which define samples"
          "(def. the 'src_dataset')")
)
@click.option(
    '--datafile',
    type=str,
    required=True,
    help="The metadata file in which search for information")
@optgroup.group(
    'Codes',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option(
    '--code_column',
    type=str,
    default="code",
    help="Code column in src datafile (ie FID)"
)
@optgroup.option(
    '--code_all',
    type=str,
    help="Code applied to all items in datafile"
)
@optgroup.group(
    'Countries',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option(
    '--country_column',
    type=str,
    default="country",
    help="Country column in src datafile"
)
@optgroup.option(
    '--country_all',
    type=str,
    help="Country applied to all items in datafile"
)
@optgroup.group(
    'Species',
    cls=MutuallyExclusiveOptionGroup
)
@optgroup.option(
    '--species_column',
    type=str,
    help="Species column in src datafile"
)
@optgroup.option(
    '--species_all',
    type=str,
    help="Species applied to all items in datafile"
)
@click.option('--id_column', type=str, required=True,
              help="The 'original_id' column to place in smarter database")
@click.option(
    '--sex_column',
    type=str,
    help="Sex column in src datafile")
@click.option(
    '--chip_name',
    type=str,
    required=True,
    help="The SMARTER SupportedChip name")
@click.option(
    '--alias_column',
    type=str,
    help="An alias for original_id")
@click.option(
    '--skip_missing_alias',
    is_flag=True,
    help="Don't import samples with no alias")
def main(
        src_dataset, dst_dataset, datafile, code_column, code_all,
        country_column, country_all, species_column, species_all,
        id_column, sex_column, chip_name, alias_column, skip_missing_alias):
    """Generate samples from a metadata file"""

    logger.info(f"{Path(__file__).name} started")

    src_dataset, dst_dataset, datapath = deal_with_datasets(
        src_dataset, dst_dataset, datafile)

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    # get sample type
    type_ = get_sample_type(dst_dataset)

    # read datafile
    data = pandas_open(datapath)

    logger.info(f"Got columns: {data.columns.to_list()}")

    for index, row in data.iterrows():
        logger.debug(f"Got: {row.to_list()}")

        # this will be the original_id
        original_id = str(row.get(id_column))

        # determine breeds and code relying on parameters
        breed, code = deal_with_breeds(code_all, code_column, dst_dataset, row)

        # determine country
        country = deal_with_countries(country_all, country_column, row)

        # assign species from parameter or from datasource column
        if species_column:
            species = row.get(species_column)

        else:
            species = species_all

        sex, alias = deal_with_sex_and_alias(
            sex_column, alias_column, row)

        logger.debug(
            f"Got code: {code}, country: {country}, breed: {breed}, "
            f"original_id: {original_id}, sex: {sex}, alias: {alias}"
        )

        if skip_missing_alias and not alias:
            logger.warning(
                f"Ignoring code: {code}, country: {country}, breed: {breed}, "
                f"original_id: {original_id}, sex: {sex}, alias: {alias}"
            )
            continue

        # get or create a new Sample Obj
        sample, created = get_or_create_sample(
            SampleSpecies=SampleSpecie,
            original_id=original_id,
            dataset=dst_dataset,
            type_=type_,
            breed=breed,
            country=country.name,
            species=species,
            chip_name=chip_name,
            sex=sex,
            alias=alias)

        if created:
            logger.info(f"Sample '{sample}' added to database")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
