#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 12:13:47 2023

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

This program acts like import_phenotypes but adding more data for the same
individual
"""

import click
import logging

from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from pathlib import Path

from src.features.smarterdb import global_connection

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--src_dataset', type=str, required=True,
    help="The raw dataset file name (zip archive) in which search datafile"
)
@click.option(
    '--dst_dataset', type=str, required=False,
    help=("The raw dataset file name (zip archive) in which add metadata"
          "(def. the 'src_dataset')")
)
@click.option('--datafile', type=str, required=True)
@click.option('--sheet_name',
              default="0",
              help="pandas 'sheet_name' option")
@optgroup.group(
    'Add metadata relying on breeds or samples columns',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option('--breed_column', type=str, help="The breed column")
@optgroup.option('--id_column', type=str, help="The original_id column")
@optgroup.option('--alias_column', type=str, help="An alias for original_id")
@click.option(
    '--column',
    required=True,
    multiple=True,
    help=(
        "Column to track. Could be specified multiple times")
)
@click.option('--na_values', type=str, help="pandas NA values")
def main(src_dataset, dst_dataset, datafile, sheet_name, breed_column,
         id_column, alias_column, column, na_values):
    """Read multiple data for the same sample from phenotype file and add it
    to SMARTER-database samples"""

    logger.info(f"{Path(__file__).name} started")

    if breed_column or alias_column:
        raise NotImplementedError(
            "Loading multiple phenotypes by breed or alias is not yet "
            "implemented")

    logger.debug(f"Reading {column} columns")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
