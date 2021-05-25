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
        row: pd.Series, columns: dict, label: str):
    """Function to get info from column which are declared attributes in
    smarterdb"""

    # those are columns which are modelled in database
    attr2keys = {
        'purpose': 'purpose_column',
        'chest_girth': 'chest_girth_column',
        'height': 'height_column',
        'length': 'length_column',
    }

    results = dict()

    for key, column_name in attr2keys.items():
        if columns[column_name]:
            value = row.get(columns[column_name])
            if pd.notnull(value) and pd.notna(value):
                logger.debug(
                    f"Got '{key}': '{value}' for '{label}'")
                results[key] = value

    return results


def get_additional_column(row: pd.Series, columns: dict, label: str):
    additional_column = dict()

    if columns["additional_column"]:
        for column in columns["additional_column"]:
            if pd.notnull(row.get(column)):
                additional_column[sanitize(column)] = row.get(column)

        logger.debug(
            f"Got additional_column: '{additional_column}' for '{label}'")

    return additional_column


def create_or_update_phenotype(
        sample, named_columns: dict, additional_column: dict):

    if not additional_column and not named_columns:
        logger.debug(f"Skipping {sample}: nothing to update")
        return

    if not sample.phenotype:
        logger.debug(f"Create a new phenotype for {sample}")
        sample.phenotype = Phenotype()

    for key, value in named_columns.items():
        setattr(sample.phenotype, key, value)

    # set all the other not managed phenotypes colums
    if additional_column:
        for key, value in additional_column.items():
            setattr(sample.phenotype, key, value)

    logger.info(
        f"Updating '{sample}' phenotype with '{sample.phenotype}'")

    # update sample
    sample.save()


def add_phenotype_by_breed(
        data: pd.DataFrame,
        dst_dataset: Dataset,
        columns: dict):
    """Add metadata relying on breed name (column)"""

    logger.debug(f"Received columns: {columns}")

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    for index, row in data.iterrows():
        logger.debug(f"{index}, {row}")
        breed = row.get(columns["breed_column"])

        # get columns modelled in smarter database
        named_columns = get_named_columns(row, columns, breed)

        # get additional columns for breed
        additional_column = get_additional_column(row, columns, breed)

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dst_dataset, breed=breed):

            create_or_update_phenotype(
                sample, named_columns, additional_column)


def add_phenotype_by_sample(
        data: pd.DataFrame,
        dst_dataset: Dataset,
        columns: dict):
    """Add metadata relying on breed name (column)"""

    logger.debug(f"Received columns: {columns}")

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    for index, row in data.iterrows():
        logger.debug(f"{index}, {row}")
        original_id = row.get(columns["id_column"])

        # get columns modelled in smarter database
        named_columns = get_named_columns(row, columns, original_id)

        # get additional columns for breed
        additional_column = get_additional_column(row, columns, original_id)

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dst_dataset, original_id=original_id):

            create_or_update_phenotype(
                sample, named_columns, additional_column)


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
@click.option('--sheet_name',
              default="0",
              help="pandas 'sheet_name' option")
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
def main(src_dataset, dst_dataset, datafile, sheet_name, breed_column,
         id_column, purpose_column, chest_girth_column, height_column,
         length_column, additional_column, na_values):
    logger.info(f"{Path(__file__).name} started")

    if additional_column:
        logger.debug(f"Got {additional_column} as additional phenotype")

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

    if sheet_name and sheet_name.isnumeric():
        sheet_name = int(sheet_name)

    # open data with pandas
    data = pandas_open(datapath, na_values=na_values, sheet_name=sheet_name)

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
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()