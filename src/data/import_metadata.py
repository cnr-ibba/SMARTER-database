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

from pathlib import Path
import pandas as pd

from src.features.smarterdb import global_connection, SampleSheep
from src.data.common import fetch_and_check_dataset
from src.features.utils import sanitize

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
@click.option('--datafile', type=str, required=True)
@click.option('--breed_column', type=str, default="breed")
@click.option('--latitude_column', type=str)
@click.option('--longitude_column', type=str)
@click.option('--metadata_column', multiple=True, help=(
    "Metadata column to track. Could be specified multiple times"))
def main(dataset, datafile, breed_column, latitude_column, longitude_column,
         metadata_column):
    logger.info(f"{Path(__file__).name} started")

    logger.warning(metadata_column)

    # custom method to check a dataset and ensure that needed stuff exists
    dataset, [datapath] = fetch_and_check_dataset(
        archive=dataset,
        contents=[datafile]
    )

    # mind dataset species
    if dataset.species == 'Sheep':
        SampleSpecie = SampleSheep

    else:
        raise NotImplementedError(
            f"'{dataset.species}' import not yet implemented")

    with open(datapath, "rb") as handle:
        data = pd.read_excel(handle)

    for index, row in data.iterrows():
        breed = row.get(breed_column)
        location = None
        metadata = dict()

        if latitude_column and longitude_column:
            latitude = row.get(latitude_column)
            longitude = row.get(longitude_column)

            location = (longitude, latitude)

            logger.info(f"Got location '{location}' for '{breed}'")

        if metadata_column:
            for column in metadata_column:
                if pd.notnull(row.get(column)):
                    metadata[sanitize(column)] = row.get(column)

            logger.info(f"Got metadata: '{metadata}' for '{breed}'")

        # ok iterate over all samples of this dataset
        for sample in SampleSpecie.objects.filter(
                dataset=dataset, breed=breed):

            logger.info(f"Updating '{sample}'")

            # set location features
            sample.location = location

            # set metadata if necessary
            if metadata:
                sample.metadata = metadata

            # update sample
            sample.save()

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    # connect to database
    global_connection()

    main()
