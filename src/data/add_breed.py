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

from src.features.smarterdb import global_connection, Breed

logger = logging.getLogger(__name__)


@click.command()
@click.option('--species', type=str, required=True)
@click.option('--name', type=str, required=True)
@click.option('--code', type=str, required=True)
@click.option('--alias', type=str, multiple=True)
def main(species, name, code, alias):
    """Add or update a breed into SMARTER database"""

    logger.info(f"{Path(__file__).name} started")

    # fix input parameters
    aliases = alias
    species = species.capitalize()
    name = name.capitalize()
    code = code.upper()

    # get a breed object relying on parameters
    qs = Breed.objects(species=species, name=name, code=code)

    if qs.count() == 1:
        breed = qs.get()
        logger.debug(f"Got {breed}")
        for alias in aliases:
            if alias not in breed.aliases:
                logger.info(f"Adding {alias} to {breed} aliases")
                breed.aliases.append(alias)

    elif qs.count() == 0:
        logger.info("Create a new breed object")
        breed = Breed(
            species=species,
            name=name,
            code=code,
            aliases=aliases,
            n_individuals=0
        )

    # update a breed object
    logger.info("Updating database")
    breed.save()

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
