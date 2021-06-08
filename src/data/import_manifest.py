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

from src.features.illumina import read_Manifest
from src.features.smarterdb import (
    VariantSheep, Location, global_connection, IlluminaChip, VariantGoat)
from src.data.common import get_variant_species

logger = logging.getLogger(__name__)


@click.command()
@click.option('--species', type=str, required=True)
@click.option('--manifest', type=str, required=True)
@click.option('--chip_name', type=str, required=True)
@click.option('--version', type=str, required=True)
@click.option('--sender', type=str, required=True)
def main(species, manifest, chip_name, version, sender):
    # determining the proper VariantSpecies class
    VariantSpecie = get_variant_species(species)

    # check chip_name
    illumina_chip = IlluminaChip.objects(name=chip_name).get()

    # reset chip data (if any)
    illumina_chip.n_of_snps = 0

    logger.info(f"Reading from {manifest}")

    # grep a sample SNP
    for i, record in enumerate(read_Manifest(manifest, delimiter=",")):
        # update chip data indipendentely if it is an update or not
        illumina_chip.n_of_snps += 1

        # create a location object
        location = Location(
            version=version,
            chrom=record.chr,
            position=record.mapinfo,
            illumina=record.snp,
            illumina_strand=record.ilmnstrand,
            strand=record.sourcestrand,
            imported_from="manifest",
            date=record.date,
        )

        variant = VariantSpecie(
            chip_name=[chip_name],
            name=record.name,
            sequence=record.sourceseq,
            sender=sender
        )

        # search for a snp in database (relying on name)
        qs = VariantSpecie.objects.filter(name=record.name)

        if qs.count() == 1:
            update_variant(qs, variant, location)

        elif qs.count() == 0:
            new_variant(variant, location)

        if (i+1) % 5000 == 0:
            logger.info(f"{i+1} variants processed")

    # update chip info
    illumina_chip.save()

    logger.info(f"{i+1} variants processed")

    logger.info("Completed")


def update_variant(
        qs: QuerySet,
        variant: Union[VariantSheep, VariantGoat],
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

    # HINT: should I update location?
    else:
        logger.warning(
            f"Locations differ: {location} <> {variant.locations[index]}")


def new_variant(
        variant: Union[VariantSheep, VariantGoat],
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
