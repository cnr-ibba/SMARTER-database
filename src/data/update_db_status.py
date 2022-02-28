#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 18:18:26 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging
import datetime

from pathlib import Path

from mongoengine.errors import DoesNotExist

from src import __version__
from src.data.common import WORKING_ASSEMBLIES, PLINK_SPECIES_OPT
from src.features.smarterdb import (
    global_connection, SmarterInfo, SampleSheep, SampleGoat, CountrySheep,
    CountryGoat)

logger = logging.getLogger(__name__)


def update_countries_collection():
    """After all data is loaded and samples created, get all countries and
    makes a collection respectively for Sheep and goats, in order to help
    user while searching from their samples"""

    logger.debug("Dropping country collections")

    # drop old country collection
    CountrySheep.drop_collection()
    CountryGoat.drop_collection()

    logger.info("Updating country collections")

    # get distinct countries from samples
    sheep_countries = SampleSheep.objects.distinct("country")

    for country_name in sheep_countries:
        country = CountrySheep(name=country_name)
        country.save()

    goat_countries = SampleGoat.objects.distinct("country")

    for country_name in goat_countries:
        country = CountryGoat(name=country_name)
        country.save()

    logger.info("Done!")


@click.command()
def main():
    """Update SMARTER database statuses"""

    logger.info(f"{Path(__file__).name} started")

    try:
        database = SmarterInfo.objects.get(id="smarter")
        logger.debug(f"Found: {database}")

    except DoesNotExist:
        logger.warning("Smarter database status was never tracked")
        database = SmarterInfo(id="smarter")

    # update collections
    update_countries_collection()

    # update stuff
    database.version = __version__
    database.working_assemblies = WORKING_ASSEMBLIES
    database.plink_specie_opt = PLINK_SPECIES_OPT
    database.last_updated = datetime.datetime.now()

    database.save()

    logger.info("Database status updated")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
