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
@click.option('--code_column', type=str, default="code")
@click.option('--country_column', type=str, default="country")
@click.option('--id_column', type=str, required=True,
              help="The 'original_id' column to place in smarter database")
@click.option('--sex_column', type=str)
@click.option('--chip_name', type=str, required=True)
def main(
        src_dataset, dst_dataset, datafile, code_column, country_column,
        id_column, sex_column, chip_name):
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
        code = row.get(code_column)
        country = row.get(country_column)
        original_id = row.get(id_column)
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

        # process a country by doing a fuzzy search
        # HINT: this function cache results relying arguments using lru_cache
        # see find country implementation for more informations
        country = find_country(country)

        # get breed from database
        breed = Breed.objects(
            aliases__match={'fid': code, 'dataset': dst_dataset}).get()

        logger.debug(f"found breed '{breed}'")

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
