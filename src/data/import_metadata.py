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

from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from pathlib import Path
import pandas as pd

from src.features.smarterdb import global_connection, Dataset
from src.data.common import (
    fetch_and_check_dataset, pandas_open, get_sample_species)
from src.features.utils import sanitize

logger = logging.getLogger(__name__)


def add_metadata_by_breed(
        data: pd.DataFrame,
        dst_dataset: Dataset,
        columns: dict):
    """Add metadata relying on breed name (column)"""

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    for index, row in data.iterrows():
        breed = row.get(columns["breed_column"])
        location = None
        metadata = dict()

        if columns["latitude_column"] and columns["longitude_column"]:
            latitude = row.get(columns["latitude_column"])
            longitude = row.get(columns["longitude_column"])

            if pd.notna(latitude) and pd.notna(longitude):
                location = (longitude, latitude)

            logger.info(f"Got location '{location}' for '{breed}'")

        if columns["metadata_column"]:
            for column in columns["metadata_column"]:
                if pd.notnull(row.get(column)):
                    metadata[sanitize(column)] = row.get(column)

            logger.info(f"Got metadata: '{metadata}' for '{breed}'")

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dst_dataset, breed=breed):

            logger.info(f"Updating '{sample}'")

            # set location features
            sample.location = location

            # set metadata if necessary
            if metadata:
                sample.metadata = metadata

            # update sample
            sample.save()


def add_metadata_by_sample(
        data: pd.DataFrame,
        dst_dataset: Dataset,
        columns: dict):
    """Add metadata relying on breed name (column)"""

    # mind dataset species
    SampleSpecie = get_sample_species(dst_dataset.species)

    for index, row in data.iterrows():
        original_id = row.get(columns["id_column"])
        location = None
        metadata = dict()

        if columns["latitude_column"] and columns["longitude_column"]:
            latitude = row.get(columns["latitude_column"])
            longitude = row.get(columns["longitude_column"])

            if pd.notna(latitude) and pd.notna(longitude):
                location = (longitude, latitude)

            logger.info(f"Got location '{location}' for '{original_id}'")

        if columns["metadata_column"]:
            for column in columns["metadata_column"]:
                if pd.notnull(row.get(column)):
                    metadata[sanitize(column)] = row.get(column)

            logger.info(f"Got metadata: '{metadata}' for '{original_id}'")

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dst_dataset, original_id=original_id):

            logger.info(f"Updating '{sample}'")

            # set location features
            sample.location = location

            # set metadata if necessary
            if metadata:
                sample.metadata = metadata

            # update sample
            sample.save()


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
@click.option('--latitude_column', type=str)
@click.option('--longitude_column', type=str)
@click.option('--metadata_column', multiple=True, help=(
    "Metadata column to track. Could be specified multiple times"))
@click.option('--na_values', type=str, help="pandas NA values")
def main(src_dataset, dst_dataset, datafile, breed_column, id_column,
         latitude_column, longitude_column, metadata_column, na_values):
    logger.info(f"{Path(__file__).name} started")

    if metadata_column:
        logger.warning(f"Got {metadata_column} as additional metadata")

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
        'latitude_column': latitude_column,
        'longitude_column': longitude_column,
        'metadata_column': metadata_column,
    }

    if breed_column:
        add_metadata_by_breed(data, dst_dataset, columns)

    elif id_column:
        add_metadata_by_sample(data, dst_dataset, columns)

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    # connect to database
    global_connection()

    main()
