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
from datetime import datetime

from src.features.utils import get_interim_dir, get_processed_dir
from src.features.smarterdb import global_connection, Dataset, SPECIES2CODE

logger = logging.getLogger(__name__)


@click.command()
@click.option('--species', type=str, required=True)
@click.option('--assembly', type=str, required=True)
def main(species, assembly):
    logger.info(f"{Path(__file__).name} started")

    # connect to database
    global_connection()

    # get time
    now = datetime.now()

    # open a file to track files to merge
    smarter_tag = "SMARTER-{specie}-{assembly}-top-{version}".format(
        specie=SPECIES2CODE[species.capitalize()],
        assembly=assembly.upper(),
        version=now.strftime("%Y%m%d")
    )
    merge_file = get_interim_dir() / smarter_tag

    with merge_file.open(mode="w") as handle:
        for dataset in Dataset.objects(species=species.capitalize()):
            logger.debug(f"Got {dataset}")

            # search for result dir
            results_dir = Path(dataset.result_dir) / assembly.upper()

            if results_dir.exists():
                logger.info(f"Found {results_dir}")

                # search for bed files
                bed_files = list(results_dir.glob('*.bed'))

                if len(bed_files) != 1:
                    raise Exception(
                        f"Couldn't define a unique bed file for {dataset}: "
                        f"{bed_files}"
                    )

                # determine the bedfile full path
                bed_file = results_dir / bed_files[0].stem

                # track file to merge
                handle.write(f"{bed_file}\n")

    # ok check for results dir
    final_dir = get_processed_dir() / "OARV3"
    final_dir.mkdir(parents=True, exist_ok=True)

    # ok time to convert data in plink binary format
    cmd = [
        "plink",
        f"--{species.lower()}",
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

    main()
