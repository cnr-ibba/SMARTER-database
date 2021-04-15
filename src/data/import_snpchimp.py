#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 10:38:05 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging

from src.features.snpchimp import read_snpChimp
from src.features.smarterdb import (
    VariantSheep, Location, global_connection, SmarterDBException)

logger = logging.getLogger(__name__)


@click.command()
@click.option('--species', type=str, required=True)
@click.option('--snpchimp', type=str, required=True)
@click.option('--version', type=str, required=True)
def main(species, snpchimp, version):
    # fix input parameters
    species = species.capitalize()

    if species == 'Sheep':
        VariantSpecie = VariantSheep

    else:
        raise NotImplementedError(f"'{species}' import not yet implemented")

    logger.info(f"Reading from {snpchimp}")

    # grep a sample SNP
    for i, snpchimp in enumerate(read_snpChimp(snpchimp)):
        # get a variant from database (I suppose to have a variant for
        # each snpchimp record)
        variant = VariantSpecie.objects.get(name=snpchimp.snp_name)

        # read location from SnpChimp data
        location = Location(
            ss_id=snpchimp.ss,
            version=version,
            chrom=snpchimp.chromosome,
            position=snpchimp.position,
            illumina_top=snpchimp.alleles_a_b_top,
            illumina_forward=snpchimp.alleles_a_b_forward,
            illumina_strand=snpchimp.strand,
            strand=snpchimp.orient,
            alleles=snpchimp.alleles,
            imported_from="SNPchiMp v.3"
        )

        # Should I update a location or not?
        if not check_and_update_location(location, variant):
            logger.warning(snpchimp)

        else:
            # update variant with snpchimp data
            variant.rs_id = snpchimp.rs
            variant.save()

        if (i+1) % 5000 == 0:
            logger.info(f"{i+1} variants processed")

    logger.info(f"{i+1} variants processed")

    logger.info("Completed")


def check_and_update_location(location, variant) -> bool:
    # get the old location as index
    try:
        index = variant.get_location_index(
            version=location.version, imported_from=location.imported_from)

    except SmarterDBException as exc:
        # if a index does not exist, then insert feature without warnings
        logger.debug(exc)
        variant.locations.append(location)
        return True

    # ok get the old location and check with the new one
    if variant.locations[index] == location:
        logger.debug(f"Locations match {location}")
        return True

    else:
        logger.warning(
            f"Locations differ for '{variant.name}': {location} <> "
            f"{variant.locations[index]}"
        )

        variant.locations[index] = location
        logger.warning(
            f"Updating {variant}")

        return False


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
