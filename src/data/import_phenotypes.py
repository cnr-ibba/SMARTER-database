#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 11 12:11:45 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging

from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from pathlib import Path
import pandas as pd

from src.features.smarterdb import global_connection, Dataset, Phenotype
from src.data.common import (
    fetch_and_check_dataset, pandas_open, get_sample_species)
from src.features.utils import sanitize

logger = logging.getLogger(__name__)


def get_named_columns(
        row: pd.Series, key: str, columns: dict, label: str):
    """Generic function to get info from column for declared attributes"""

    result = None

    if columns[key]:
        value = row.get(columns[key])
        if pd.notnull(value) and pd.notna(value):
            result = value

    return result


def get_additional_column(row: pd.Series, columns: dict, label: str):
    additional_column = dict()

    if columns["additional_column"]:
        for column in columns["additional_column"]:
            if pd.notnull(row.get(column)):
                additional_column[sanitize(column)] = row.get(column)

        logger.debug(
            f"Got additional_column: '{additional_column}' for '{label}'")

    return additional_column


def add_phenotype_by_breed(
        data: pd.DataFrame,
        dst_dataset: Dataset,
        columns: dict):
    """Add metadata relying on breed name (column)"""

    logger.warning(f"Received columns: {columns}")

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    for index, row in data.iterrows():
        breed = row.get(columns["breed_column"])
        purpose = get_named_columns(row, 'purpose_column', columns, breed)
        chest_girth = get_named_columns(
            row, 'chest_girth_column', columns, breed)
        height = get_named_columns(row, 'height_column', columns, breed)
        length = get_named_columns(row, 'length_column', columns, breed)

        # get additional columns for breed
        additional_column = get_additional_column(row, columns, breed)

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dst_dataset, breed=breed):

            if not sample.phenotype:
                sample.phenotype = Phenotype()

            sample.phenotype.purpose = purpose
            sample.phenotype.chest_girth = chest_girth
            sample.phenotype.height = height
            sample.phenotype.length = length

            # set all the other not managed phenotypes colums
            if additional_column:
                for key, value in additional_column.items():
                    setattr(sample.phenotype, key, value)

            logger.warning(
                f"Updating '{sample}' phenotype with '{sample.phenotype}'")

            # update sample
            sample.save()


def add_phenotype_by_sample(
        data: pd.DataFrame,
        dst_dataset: Dataset,
        columns: dict):
    """Add metadata relying on breed name (column)"""

    raise NotImplementedError(
        "Adding phenotype by sample_id is not yet implemented")


@click.command()
@click.option(
    '--src_dataset', type=str, required=True,
    help="The raw dataset file name (zip archive) in which search datafile"
)
@click.option(
    '--dst_dataset', type=str, required=True,
    help="The raw dataset file name (zip archive) in which add metadata"
)
@click.option('--datafile', type=str, required=True)
@optgroup.group(
    'Add metadata relying on breeds or samples columns',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option('--breed_column', type=str, help="The breed column")
@optgroup.option('--id_column', type=str, help="The original_id column")
@click.option('--purpose_column', type=str)
@click.option('--chest_girth_column', type=str)
@click.option('--height_column', type=str)
@click.option('--length_column', type=str)
@click.option('--additional_column', multiple=True, help=(
    "Additional column to track. Could be specified multiple times"))
@click.option('--na_values', type=str, help="pandas NA values")
def main(src_dataset, dst_dataset, datafile, breed_column, id_column,
         purpose_column, chest_girth_column, height_column, length_column,
         additional_column, na_values):
    logger.info(f"{Path(__file__).name} started")

    if additional_column:
        logger.warning(f"Got {additional_column} as additional phenotype")

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

    # open data with pandas
    data = pandas_open(datapath, na_values=na_values)

    # collect columns in a dictionary
    columns = {
        'breed_column': breed_column,
        'id_column': id_column,
        'purpose_column': purpose_column,
        'chest_girth_column': chest_girth_column,
        'height_column': height_column,
        'length_column': length_column,
        'additional_column': additional_column,
    }

    if breed_column:
        add_phenotype_by_breed(data, dst_dataset, columns)

    elif id_column:
        add_phenotype_by_sample(data, dst_dataset, columns)

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    # connect to database
    global_connection()

    main()
