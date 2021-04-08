#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 10:38:05 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging

from typing import Union

from mongoengine.errors import NotUniqueError
from mongoengine.queryset import QuerySet

from src.features.illumina import read_snpChip
from src.features.smarterdb import VariantSheep, Location, global_connection

logger = logging.getLogger(__name__)


@click.command()
@click.option('--species', type=str, required=True)
@click.option('--manifest', type=str, required=True)
@click.option('--chip_name', type=str, required=True)
@click.option('--version', type=str, required=True)
@click.option('--sender', type=str, required=True)
def main(species, manifest, chip_name, version, sender):
    # fix input parameters
    species = species.capitalize()

    if species == 'Sheep':
        VariantSpecie = VariantSheep

    else:
        raise NotImplementedError(f"'{species}' import not yet implemented")

    logger.info(f"Reading from {manifest}")

    # grep a sample SNP
    for i, snpchip in enumerate(read_snpChip(manifest)):
        # create a location object
        location = Location(
            version=version,
            chrom=snpchip.chr,
            position=snpchip.mapinfo,
            illumina=snpchip.snp,
            illumina_strand=snpchip.ilmnstrand,
            strand=snpchip.sourcestrand,
            imported_from="manifest"
        )

        variant = VariantSpecie(
            chip_name=[chip_name],
            name=snpchip.name,
            sequence=snpchip.sourceseq,
            sender=sender
        )

        # search for a snp in database (relying on name)
        qs = VariantSpecie.objects.filter(name=snpchip.name)

        if qs.count() == 1:
            update_variant(qs, variant, location)

        elif qs.count() == 0:
            new_variant(variant, location)

        # queryset block

    logger.info("Completed")


def update_variant(
        qs: QuerySet,
        variant: Union[VariantSheep],  # will model also VariantGoat
        location: Location):
    """Update an existing variant (if necessary)"""

    record = qs.get()
    logger.debug(f"found {record} in database")

    # check chip_name in variant list
    record = update_chip_name(variant, record)

    # I chose to not update other values, I suppose they be the same
    # However check for locations
    check_location(location, record)


def update_chip_name(variant, record):
    variant_set = set(variant.chip_name)
    record_set = set(record.chip_name)

    # get new items as a difference of two sets
    new_chips = variant_set - record_set

    if len(new_chips) > 0:
        # this will append the resulting set as a list
        record.chip_name += list(new_chips)
        record.save()

    return record


def check_location(location, variant):
    # get the old location as index
    index = variant.get_location_index(
        version=location.version, imported_from=location.imported_from)

    # ok get the old location and check with the new one
    if variant.locations[index] == location:
        logger.debug("Locations match")

    else:
        logger.warning(
            f"Locations differ: {location} <> {variant.locations[index]}")


def new_variant(
        variant: Union[VariantSheep],  # will model also VariantGoat
        location: Location):

    variant.locations.append(location)

    logger.info(f"adding {variant} to database")

    try:
        variant.save()

    except NotUniqueError as e:
        logger.error(
            f"Cannot insert {variant}, reason: {e}")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
