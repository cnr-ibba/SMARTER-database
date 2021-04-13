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

import click
import logging
import subprocess

from pathlib import Path

from src.features.plinkio import IlluminaReportIO
from src.features.smarterdb import Dataset, global_connection

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

    # check files are in dataset
    if snpfile not in dataset.contents or report not in dataset.contents:
        logger.critical(
            "Couldn't find files in dataset: check for both "
            f"'{snpfile}' and '{report}' in '{dataset}'")
        return

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        logger.critical(f"Could find dataset directory {working_dir}")
        return

    # determine full file paths
    snpfilepath = working_dir / snpfile
    reportpath = working_dir / report

    # instantiating a TextPlinkIO object
    report = IlluminaReportIO(
        snpfile=snpfilepath,
        report=reportpath,
        species=dataset.species
    )

    # set mapdata and read updated coordinates from db
    report.read_snpfile()
    report.fetch_coordinates(version="Oar_v3.1")

    logger.info("Writing a new map file with updated coordinates")

    output_dir = working_dir / "OARV3"
    output_dir.mkdir(exist_ok=True)
    output_map = Path(reportpath).stem + "_updated.map"
    output_map = output_dir / output_map

    report.update_mapfile(str(output_map))

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
