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
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

import pycountry

from src.data.common import (
    fetch_and_check_dataset, pandas_open, get_sample_species)
from src.features.smarterdb import (
    global_connection, Breed, get_or_create_sample, SEX)

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

    # transform country string with pycountry
    fuzzy = pycountry.countries.search_fuzzy(country)[0]

    logger.info(f"Found {fuzzy} for {country}")

    return fuzzy


@click.command()
@click.option(
    '--src_dataset', type=str, required=True,
    help="The raw dataset file name (zip archive) in which search datafile"
)
@click.option(
    '--dst_dataset', type=str, required=True,
    help="The raw dataset file name (zip archive) in which define samples"
)
@click.option('--datafile', type=str, required=True)
@optgroup.group(
    'Codes',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option(
    '--code_column',
    type=str,
    default="code",
    help="Code column in src datafile"
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
@click.option('--id_column', type=str, required=True,
              help="The 'original_id' column to place in smarter database")
@click.option('--sex_column', type=str)
@click.option('--chip_name', type=str, required=True)
def main(
        src_dataset, dst_dataset, datafile, code_column, code_all,
        country_column, country_all, id_column, sex_column, chip_name):
    logger.info(f"{Path(__file__).name} started")

    # custom method to check a dataset and ensure that needed stuff exists
    src_dataset, [datapath] = fetch_and_check_dataset(
        archive=src_dataset,
        contents=[datafile]
    )

    # this will be the dataset used to define samples
    dst_dataset, _ = fetch_and_check_dataset(
        archive=dst_dataset,
        contents=[]
    )

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    # read datafile
    data = pandas_open(datapath)

    logger.info(f"Got columns: {data.columns.to_list()}")

    for index, row in data.iterrows():
        logger.debug(f"Got: {row.to_list()}")

        # this will be the original_id
        original_id = row.get(id_column)

        # assign code from parameter or from datasource column
        if code_all:
            code = code_all

            # get breed from database
            breed = Breed.objects(code=code).get()

        else:
            code = row.get(code_column)

            # get breed from database
            breed = Breed.objects(
                aliases__match={'fid': code, 'dataset': dst_dataset}).get()

        logger.debug(f"found breed '{breed}'")

        # assign country from parameter or from datasource column
        if country_all:
            country = country_all

        else:
            country = row.get(country_column)

        # process a country by doing a fuzzy search
        # HINT: this function cache results relying arguments using lru_cache
        # see find country implementation for more informations
        country = find_country(country)

        # Have I sex? search for a sex column if provided
        sex = None

        if sex_column:
            sex = str(row.get(sex_column))
            sex = SEX.from_string(sex)

            # drop sex column if unknown
            if sex == SEX.UNKNOWN:
                sex = None

        logger.debug(
            f"Got code: {code}, country: {country}, "
            f"original_id: {original_id}, sex: {sex}"
        )

        # get or create a new Sample Obj
        sample, created = get_or_create_sample(
            SampleSpecie,
            original_id,
            dst_dataset,
            breed,
            country.name,
            chip_name,
            sex)

        if created:
            logger.info(f"Sample '{sample}' added to database")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
