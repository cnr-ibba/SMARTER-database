#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 15:08:13 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Attempt to add additional metadata to Smarter Samples. Could add metadata
realying on breeds (all the samples in a dataset with the same breed) or by
each sample
"""

import click
import logging
import itertools

from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from pathlib import Path
import pandas as pd

from src.features.smarterdb import global_connection, Dataset
from src.data.common import (
    deal_with_datasets, pandas_open, get_sample_species)
from src.features.utils import sanitize

logger = logging.getLogger(__name__)


def strip_multiple_values(value: str):
    results = []

    logger.debug(f"Received: '{value}'")

    if isinstance(value, str):
        tmp = sanitize(value, chars=["-", "/"])
        results = [float(val) for val in tmp.split("_")]

    else:
        results = [value]

    return results


def get_locations(row: pd.Series, columns: dict, label: str):
    locations = None

    if columns["latitude_column"] and columns["longitude_column"]:
        latitude = row.get(columns["latitude_column"])
        longitude = row.get(columns["longitude_column"])

        if pd.notna(latitude) and pd.notna(longitude):
            latitude = strip_multiple_values(latitude)
            longitude = strip_multiple_values(longitude)

            locations = list(itertools.zip_longest(longitude, latitude))

        logger.debug(f"Got locations '{locations}' for '{label}'")

    return locations


def get_metadata(row: pd.Series, columns: dict, label: str):
    metadata = dict()

    if columns["metadata_column"]:
        for column in columns["metadata_column"]:
            if pd.notnull(row.get(column)):
                metadata[sanitize(column)] = row.get(column)

        logger.debug(f"Got metadata: '{metadata}' for '{label}'")

    return metadata


def add_metadata_by_breed(
        data: pd.DataFrame,
        dst_dataset: Dataset,
        columns: dict):
    """Add metadata relying on breed name (column)"""

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    for index, row in data.iterrows():
        breed = row.get(columns["breed_column"])

        # get additional columns for breed
        locations = get_locations(row, columns, breed)
        metadata = get_metadata(row, columns, breed)

        logger.debug(
            f"Got breed: '{breed}', locations: {locations}, "
            f"metadata: {metadata}"
        )

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dst_dataset, breed=breed):

            # set locations features
            sample.locations = locations

            # set metadata if necessary
            if metadata:
                sample.metadata = metadata

            logger.info(
                f"Updating '{sample}' with locations: '{locations}' "
                f"and metadata: '{metadata}'")

            # update sample
            sample.save()


def add_metadata_by_sample(
        data: pd.DataFrame,
        dst_dataset: Dataset,
        columns: dict,
        id_field="id_column"):
    """Add metadata relying on original_id or alias"""

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    for index, row in data.iterrows():
        sample_id = str(row.get(columns[id_field]))

        # get additional columns for original_id
        locations = get_locations(row, columns, sample_id)
        metadata = get_metadata(row, columns, sample_id)

        logger.debug(
            f"Got {id_field}: '{sample_id}', locations: {locations}, "
            f"metadata: {metadata}"
        )

        # prepare query kwargs
        if id_field == 'id_column':
            query = {'original_id': sample_id}

        elif id_field == 'alias_column':
            query = {'alias': sample_id}

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dst_dataset, **query):

            # set locations features
            sample.locations = locations

            # set metadata if necessary
            if metadata:
                sample.metadata = metadata

            logger.info(
                f"Updating '{sample}' with locations: '{locations}' "
                f"and metadata: '{metadata}'")

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
@click.option(
    '--sheet_name',
    default="0",
    help="pandas 'sheet_name' option")
@optgroup.group(
    'Add metadata relying on breeds or samples columns',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option('--breed_column', type=str, help="The breed column")
@optgroup.option('--id_column', type=str, help="The original_id column")
@optgroup.option('--alias_column', type=str, help="The alias column")
@click.option('--latitude_column', type=str)
@click.option('--longitude_column', type=str)
@click.option('--metadata_column', multiple=True, help=(
    "Metadata column to track. Could be specified multiple times"))
@click.option('--na_values', type=str, help="pandas NA values")
def main(
        src_dataset, dst_dataset, datafile, sheet_name, breed_column,
        id_column, alias_column, latitude_column, longitude_column,
        metadata_column, na_values):
    """Read data from metadata file and add it to SMARTER-database samples"""

    logger.info(f"{Path(__file__).name} started")

    if metadata_column:
        logger.info(f"Got {metadata_column} as additional metadata")

    src_dataset, dst_dataset, datapath = deal_with_datasets(
        src_dataset, dst_dataset, datafile)

    if sheet_name and sheet_name.isnumeric():
        sheet_name = int(sheet_name)

    # open data with pandas
    data = pandas_open(datapath, na_values=na_values, sheet_name=sheet_name)

    # collect columns in a dictionary
    columns = {
        'breed_column': breed_column,
        'id_column': id_column,
        'latitude_column': latitude_column,
        'longitude_column': longitude_column,
        'metadata_column': metadata_column,
        'alias_column': alias_column,
    }

    if breed_column:
        add_metadata_by_breed(data, dst_dataset, columns)

    elif id_column:
        add_metadata_by_sample(data, dst_dataset, columns, "id_column")

    elif alias_column:
        add_metadata_by_sample(data, dst_dataset, columns, "alias_column")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
