#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 10:36:56 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import click
import logging
import itertools

from pathlib import Path
from mongoengine.queryset.visitor import Q

from src.features.smarterdb import (
    global_connection, Dataset, Breed, SampleSheep)

logger = logging.getLogger(__name__)


@click.command()
@click.option('--mapfile', type=str, required=True)
@click.option('--pedfile', type=str, required=True)
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
def main(mapfile, pedfile, dataset):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """

    logger.info(f"{Path(__file__).name} started")

    # connect to database
    global_connection()

    # get the dataset object
    dataset = Dataset.objects(file=dataset).get()

    logger.debug(f"Found {dataset}")

    # determine the SampleClass
    if dataset.species == 'Sheep':
        SampleSpecies = SampleSheep
    else:
        raise NotImplementedError(
            f"Species '{dataset.species}' not yet implemented"
        )

    # check files are in dataset
    if mapfile not in dataset.contents or pedfile not in dataset.contents:
        logger.critical(
            "Couldn't find files in dataset: check for both "
            f"'{mapfile}' and '{pedfile}' in '{dataset}'")
        return

    # check for working directory
    working_dir = project_dir / f"data/interim/{dataset.id}"
    if not working_dir.exists():
        logger.critical("Could find dataset directory {working_dir}")
        return

    # determine full file paths
    mappath = working_dir / mapfile
    pedpath = working_dir / pedfile

    sniffer = csv.Sniffer()

    # deal with map file first
    mapdata = []

    with open(mappath) as handle:
        logger.debug(f"Reading '{mappath}' content")

        dialect = sniffer.sniff(handle.read(2048))
        handle.seek(0)
        reader = csv.reader(handle, dialect=dialect)

        mapdata = list(reader)

    for line in itertools.islice(mapdata, 5):
        logger.debug(line)

    logger.info(f"Read {len(mapdata)} snps from {mappath}")

    with open(pedpath) as handle:
        logger.debug(f"Reading '{pedpath}' content")

        dialect = sniffer.sniff(handle.read(2048))
        handle.seek(0)
        reader = csv.reader(handle, dialect=dialect)

        for i, line in enumerate(reader):
            # check genotypes size 2*mapdata (diploidy) + 6 extra columns:
            if len(line) != len(mapdata)*2 + 6:
                logger.critical(
                    f"SNPs sizes don't match in '{mapfile}' and '{pedfile}'")
                logger.critical("Please check file contents")
                return

            logger.debug(f"Processing {line[:10]+ ['...']}")

            # check for breed in database
            breed = Breed.objects(
                Q(name=line[0]) | Q(aliases__in=[line[0]])
            ).get()

            logger.debug(f"Found breed {breed}")

            # search for sample in database
            qs = SampleSpecies.objects(original_id=line[1])

            if qs.count() == 1:
                logger.debug(f"Sample '{line[1]}' found in database")
                sample = qs.get()

            else:
                # TODO: insert sample into database
                logger.info(f"Registering sample '{line[1]}' in database")
                sample = SampleSheep(
                    original_id=line[1],
                    country=dataset.country,
                    species=dataset.species,
                    breed=breed.name,
                    breed_code=breed.code,
                    dataset=dataset
                )
                sample.save()

                # incrementing breed n_individuals counter
                breed.n_individuals += 1
                breed.save()

            # updating ped line with smarter ids
            line[0] = breed.code
            line[1] = sample.smarter_id

            logger.info(f"Smarter: {line[:10]+ ['...']}")

        logger.info(f"Processed {i+1} individuals")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    # this is the root of SMARTER-database project
    project_dir = Path(__file__).resolve().parents[2]

    main()
