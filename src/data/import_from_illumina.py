#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 11:56:02 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

This script will import data from illumina row format and the archive file used
while uploading the dataset in the smarter database.
Dataset country and species are mandatory and need to be
correctly defined, breed also must be loaded in database in order to define
the full smarter id like CO(untry)SP(ecies)-BREED-ID
"""

import csv
import click
import logging
import itertools
import subprocess

from pathlib import Path
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
from tqdm import tqdm

from src.features.illumina import read_snpList
from src.features.snpchimp import clean_chrom
from src.features.smarterdb import (
    global_connection, Dataset, Breed, SampleSheep, VariantSheep)
from src.features.utils import TqdmToLogger

logger = logging.getLogger(__name__)


@click.command()
@click.option('--report', type=str, required=True)
@click.option('--snpfile', type=str, required=True)
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
def main(dataset, snpfile, report):
    logger.info(f"{Path(__file__).name} started")

    # get the dataset object
    dataset = Dataset.objects(file=dataset).get()

    logger.debug(f"Found {dataset}")

    # determine the SampleClass
    if dataset.species == 'Sheep':
        SampleSpecies = SampleSheep
        VariantSpecies = VariantSheep
    else:
        raise NotImplementedError(
            f"Species '{dataset.species}' not yet implemented"
        )

    logger.info(f"{Path(__file__).name} ended")

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        logger.critical("Could find dataset directory {working_dir}")
        return

    # determine full file paths
    snpfilepath = working_dir / snpfile
    reportpath = working_dir / report

    # deal with map file first
    mapdata = list(read_snpList(snpfilepath))

    for line in itertools.islice(mapdata, 5):
        logger.debug(line)

    logger.info(f"Read {len(mapdata)} snps from {snpfilepath}")

    logger.info("Writing a new map file with updated coordinates")

    output_dir = working_dir / "OARV3"
    output_dir.mkdir(exist_ok=True)
    output_map = Path(reportpath).stem + "_updated.map"
    output_map = output_dir / output_map

    # I need to track genotypes
    locations = list()

    # need to track also filtered snps
    filtered = set()

    with open(output_map, 'w') as handle:
        writer = csv.writer(handle, delimiter=' ', lineterminator="\n")

        tqdm_out = TqdmToLogger(logger, level=logging.INFO)

        for i, line in enumerate(tqdm(mapdata, file=tqdm_out, mininterval=1)):
            try:
                # this should call the proper class relying on species
                variant = VariantSpecies.objects(name=line.name).get()

            except DoesNotExist as e:
                logger.error(f"Couldn't find {line[1]}: {e}")

                # skip this variant (even in ped)
                filtered.add(i)

                # need to add an empty value in locations (or my indexes
                # won't work properly)
                locations.append(None)

                # I don't need to write down a row in new mapfile
                continue

            # get location for snpchimp (defalt) in oarv3.1 coordinates
            # TODO: choose coordinate versions
            location = variant.get_location(version='Oar_v3.1')

            # track data for this location
            locations.append(location)

            # a new record in mapfile
            writer.writerow([
                clean_chrom(location.chrom),
                variant.name,
                0,
                location.position
            ])

    logger.debug(f"collected {len(locations)} in 'Oar_v3.1' coordinates")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
