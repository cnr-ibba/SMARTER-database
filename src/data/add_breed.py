#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 12:28:31 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Add or update a breed in smarter database using CLI
"""

import click
import logging

from pathlib import Path

from src.features.smarterdb import (
    global_connection, get_or_create_breed, BreedAlias, Dataset)

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--species_class',
    type=click.Choice(
        ['Sheep', 'Goat'],
        case_sensitive=False),
    required=True,
    help="The generic species of this breed (Sheep or Goat)")
@click.option(
    '--name',
    type=str,
    required=True,
    help="The breed name")
@click.option(
    '--code',
    type=str,
    required=True,
    help="The breed code")
@click.option(
    '--alias',
    type=str,
    multiple=True,
    help="The FID used as a breed code in genotype file")
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
def main(species_class, name, code, alias, dataset):
    """Add or update a breed into SMARTER database"""

    logger.info(f"{Path(__file__).name} started")

    # get the dataset object
    dataset = Dataset.objects(file=dataset).get()

    # fix input parameters
    aliases = [BreedAlias(fid=fid, dataset=dataset) for fid in alias]
    species_class = species_class.capitalize()
    code = code.upper()

    # get a breed object relying on parameters
    breed, modified = get_or_create_breed(
        species_class=species_class, name=name, code=code, aliases=aliases)

    if modified:
        logger.info(f"{breed} added to database")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
