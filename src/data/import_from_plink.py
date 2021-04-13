#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 10:36:56 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

This script will upload data into smarter database starting from a couple of
MAP/PED (plink) files and the archive file used for the dataset upload in the
smarter database. Dataset country and species are mandatory and need to be
correctly defined, breed also must be loaded in database in order to define
the full smarter id like CO(untry)SP(ecies)-BREED-ID
The default format is illumina top, but its possible to convert into it
from an illumina forward format
"""

import click
import logging
import subprocess

from pathlib import Path

from src.features.plinkio import TextPlinkIO
from src.features.smarterdb import Dataset, global_connection

logger = logging.getLogger(__name__)


@click.command()
@click.option('--mapfile', type=str, required=True)
@click.option('--pedfile', type=str, required=True)
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
@click.option(
    '--coding',
    type=click.Choice(
        ['top', 'forward'],
        case_sensitive=False),
    default="top", show_default=True,
    help="Illumina conding format"
)
def main(mapfile, pedfile, dataset, coding):
    """Read sample names from map/ped files and updata smarter database (insert
    a record if necessary and define a smarter id for each sample)
    """

    logger.info(f"{Path(__file__).name} started")

    # get the dataset object
    dataset = Dataset.objects(file=dataset).get()

    logger.debug(f"Found {dataset}")

    # check files are in dataset
    if mapfile not in dataset.contents or pedfile not in dataset.contents:
        logger.critical(
            "Couldn't find files in dataset: check for both "
            f"'{mapfile}' and '{pedfile}' in '{dataset}'")
        return

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        logger.critical(f"Could find dataset directory {working_dir}")
        return

    # determine full file paths
    mappath = working_dir / mapfile
    pedpath = working_dir / pedfile

    # instantiating a TextPlinkIO object
    text_plink = TextPlinkIO(
        mapfile=str(mappath),
        pedfile=str(pedpath),
        species=dataset.species
    )

    # read mapdata and read updated coordinates from db
    text_plink.read_mapfile()
    text_plink.fetch_coordinates(version="Oar_v3.1")

    logger.info("Writing a new map file with updated coordinates")

    output_dir = working_dir / "OARV3"
    output_dir.mkdir(exist_ok=True)
    output_map = Path(mapfile).stem + "_updated" + Path(mapfile).suffix
    output_map = output_dir / output_map

    text_plink.update_mapfile(str(output_map))

    # creating ped file for writing updated genotypes
    output_ped = Path(pedfile).stem + "_updated" + Path(pedfile).suffix
    output_ped = output_dir / output_ped

    text_plink.update_pedfile(output_ped, dataset, coding)

    # ok check for results dir
    results_dir = dataset.result_dir
    results_dir = results_dir / "OARV3"
    results_dir.mkdir(parents=True, exist_ok=True)

    # ok time to convert data in plink binary format
    cmd = [
        "plink",
        f"--{dataset.species.lower()}",
        "--file",
        f"{output_dir / output_ped.stem}",
        "--make-bed",
        "--out",
        f"{results_dir / output_ped.stem}"
    ]

    # debug
    logger.info("Executing: " + " ".join(cmd))

    subprocess.run(cmd, check=True)

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
