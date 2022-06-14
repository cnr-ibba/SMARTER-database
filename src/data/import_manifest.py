#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 10:38:05 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging

from src.features.illumina import read_Manifest
from src.features.smarterdb import (
    Location, global_connection, SupportedChip)
from src.data.common import get_variant_species, update_variant, new_variant

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
    illumina_chip = SupportedChip.objects(name=chip_name).get()

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
            sequence={chip_name: record.sourceseq},
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


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
