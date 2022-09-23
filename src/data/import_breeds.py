#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 16:25:15 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Import breeds from an excel template in a smarter dataset
"""

import click
import logging
from pathlib import Path

from mongoengine.errors import NotUniqueError

from src.features.smarterdb import (
    global_connection, get_or_create_breed, SmarterDBException,
    BreedAlias)
from src.data.common import deal_with_datasets, pandas_open

logger = logging.getLogger(__name__)


@click.command()
@click.option('--species_class', type=str, required=True)
@click.option(
    '--src_dataset', type=str, required=True,
    help="The raw dataset file name (zip archive) in which search datafile"
)
@click.option(
    '--dst_dataset', type=str, required=False,
    help=("The raw dataset file name (zip archive) in which define breeds"
          "(def. the 'src_dataset')")
)
@click.option('--datafile', type=str, required=True)
@click.option('--code_column', type=str, default="code")
@click.option('--breed_column', type=str, default="breed")
@click.option('--fid_column', type=str)
@click.option('--country_column', type=str)
def main(species_class, src_dataset, dst_dataset, datafile, code_column,
         breed_column, fid_column, country_column):
    logger.info(f"{Path(__file__).name} started")

    src_dataset, dst_dataset, datapath = deal_with_datasets(
        src_dataset, dst_dataset, datafile)

    # read breed into data
    data = pandas_open(datapath)

    for index, row in data.iterrows():
        code = row.get(code_column)
        name = row.get(breed_column)

        # by default, fid is equal to code
        if not fid_column:
            fid_column = code_column

        fid = row.get(fid_column)

        logger.debug(
            f"Got code: '{code}', breed_name: '{name}', "
            f"fid: '{fid}'"
        )

        # deal with multi countries dataset
        country = None

        if country_column:
            country = row.get(country_column)

        # need to define also an alias in order to retrieve such breed when
        # dealing with original file
        alias = BreedAlias(fid=fid, dataset=dst_dataset, country=country)

        try:
            breed, modified = get_or_create_breed(
                species_class=species_class,
                name=name,
                code=code,
                aliases=[alias])

            if modified:
                logger.info(f"{breed} added to database")

        except NotUniqueError as e:
            logger.error(e)
            raise SmarterDBException(
                f"Got an error while inserting '{name}'. '{code}'")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
