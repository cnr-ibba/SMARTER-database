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

from src.features.smarterdb import global_connection, Phenotype
from src.data.common import pandas_open, deal_with_datasets, get_sample_species
from src.features.utils import sanitize

logger = logging.getLogger(__name__)


def create_or_update_phenotype(
        sample, phenotype: dict):

    if not phenotype:
        logger.debug(f"Skipping {sample}: nothing to update")
        return

    if not sample.phenotype:
        logger.debug(f"Create a new phenotype for {sample}")
        sample.phenotype = Phenotype()

    for key, value in phenotype.items():
        setattr(sample.phenotype, key, value)

    logger.info(
        f"Updating '{sample}' phenotype with '{sample.phenotype}'")

    # update sample
    sample.save()


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
    'columns',
    required=True,
    multiple=True,
    help=(
        "Column to track. Could be specified multiple times")
)
@click.option('--na_values', type=str, help="pandas NA values")
def main(src_dataset, dst_dataset, datafile, sheet_name, breed_column,
         id_column, alias_column, columns, na_values):
    """Read multiple data for the same sample from phenotype file and add it
    to SMARTER-database samples"""

    logger.info(f"{Path(__file__).name} started")

    if breed_column or alias_column:
        raise NotImplementedError(
            "Loading multiple phenotypes by breed or alias is not yet "
            "implemented")

    logger.debug(f"Reading {columns} columns")

    src_dataset, dst_dataset, datapath = deal_with_datasets(
        src_dataset, dst_dataset, datafile)

    SampleSpecie = get_sample_species(dst_dataset.species)

    if sheet_name and sheet_name.isnumeric():
        sheet_name = int(sheet_name)

    # open data with pandas
    data = pandas_open(datapath, na_values=na_values, sheet_name=sheet_name)

    # process unique ids
    for id_ in data[id_column].unique():
        subset = data[data[id_column] == id_]

        phenotype = {}

        for column in columns:
            phenotype[sanitize(column)] = subset[column].to_list()

        original_id = str(id_)

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dst_dataset, original_id=original_id):

            create_or_update_phenotype(sample, phenotype)

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
