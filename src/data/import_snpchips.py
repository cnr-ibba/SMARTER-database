#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 17:31:33 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import json
import click
import logging

from pathlib import Path

from src.features.smarterdb import global_connection, IlluminaChip

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--chip_file',
    type=click.Path(exists=True),
    required=True)
def main(chip_file):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """

    logger.info(f"{Path(__file__).name} started")

    with open(chip_file) as handle:
        data = json.load(handle)

    for item in data:
        qs = IlluminaChip.objects(name=item['name'])

        if qs.count() == 0:
            chip = IlluminaChip(**item)
            chip.save()

            logger.info(f"{chip} added to database")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
