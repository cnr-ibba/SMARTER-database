#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 10:38:05 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging

from mongoengine.errors import DoesNotExist

from src.features.snpchimp import read_snpChimp
from src.features.smarterdb import (
    Location, global_connection)
from src.data.common import get_variant_species, update_location, update_rs_id

logger = logging.getLogger(__name__)


@click.command()
@click.option('--species', type=str, required=True)
@click.option('--snpchimp', type=str, required=True)
@click.option('--version', type=str, required=True)
def main(species, snpchimp, version):
    # determining the proper VariantSpecies class
    VariantSpecie = get_variant_species(species)

    logger.info(f"Reading from {snpchimp}")

    # grep a sample SNP
    for i, snpchimp in enumerate(read_snpChimp(snpchimp)):
        # get a variant from database (I suppose to have a variant for
        # each snpchimp record)
        try:
            variant = VariantSpecie.objects.get(name=snpchimp.snp_name)

        except DoesNotExist as exc:
            logger.warning(f"Skipping {snpchimp}: {exc}")

        else:
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
            update_variant = False

            variant, updated = update_location(location, variant)

            if updated:
                update_variant = True

            if snpchimp.rs:
                variant, updated = update_rs_id(
                    # create a fake variant with rs_id to use this method
                    VariantSpecie(rs_id=[snpchimp.rs]),
                    variant)

                if updated:
                    update_variant = True

            if update_variant:
                # update variant with snpchimp data
                variant.save()

        finally:
            if (i+1) % 5000 == 0:
                logger.info(f"{i+1} variants processed")

    logger.info(f"{i+1} variants processed")

    logger.info("Completed")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
