#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 23 17:11:58 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

A simple script to merge plink binary files
"""

import click
import logging
import subprocess

from pathlib import Path

from src import __version__
from src.features.utils import get_interim_dir, get_processed_dir
from src.features.smarterdb import global_connection, Dataset, SPECIES2CODE
from src.data.common import WORKING_ASSEMBLIES, PLINK_SPECIES_OPT

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--species_class',
    type=str,
    required=True,
    help=(
        "Search processed genotypes belonging to this species ('Sheep'"
        "or 'Goat')"
    )
)
@click.option(
    '--assembly',
    type=str,
    required=True,
    help="Search processed genotypes belonging to this assembly"
)
def main(species_class, assembly):
    """
    Search for processed genotype files for a certain species in
    ``data/processed`` folder and then call PLINK to join all genotypes
    in the same dataset
    """

    logger.info(f"{Path(__file__).name} started")

    # find assembly configuration
    if assembly not in WORKING_ASSEMBLIES:
        raise Exception(f"assembly {assembly} not managed by smarter")

    # open a file to track files to merge
    smarter_tag = "SMARTER-{specie}-{assembly}-top-{version}".format(
        specie=SPECIES2CODE[species_class.capitalize()],
        assembly=assembly.upper(),
        version=__version__
    )
    merge_file = get_interim_dir() / smarter_tag

    with merge_file.open(mode="w") as handle:
        for dataset in Dataset.objects(species=species_class.capitalize()):
            logger.debug(f"Got {dataset}")

            # search for result dir
            results_dir = Path(dataset.result_dir) / assembly.upper()

            if results_dir.exists():
                logger.debug(f"Found {results_dir}")

                # search for bed files
                bed_files = results_dir.glob('*.bed')

                # I can have more than 1 file for dataset (If one or more
                # files are included into dataset)
                for bed_file in bed_files:
                    # determine the bedfile full path
                    prefix = results_dir / bed_file.stem

                    logger.info(f"Appending '{prefix}' for merge")

                    # track file to merge
                    handle.write(f"{prefix}\n")

    # ok check for results dir
    final_dir = get_processed_dir() / assembly
    final_dir.mkdir(parents=True, exist_ok=True)

    # ok time to convert data in plink binary format
    cmd = ["plink"] + PLINK_SPECIES_OPT[dataset.species] + [
        "--merge-list",
        f"{merge_file}",
        "--make-bed",
        "--out",
        f"{final_dir / smarter_tag}"
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
