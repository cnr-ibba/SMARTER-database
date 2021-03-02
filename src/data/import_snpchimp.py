#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 10:38:05 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import logging

from pathlib import Path

from src.features.snpchimp import read_snpChimp
from src.features.smarterdb import VariantSheep, Location, global_connection


def main():
    logger = logging.getLogger(__name__)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    snpchimp_file = (
        "data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNP50v1_oar3.1.csv")
    snpchimp_path = project_dir / snpchimp_file

    # connect to database
    global_connection()

    logger.info(f"Reading from {snpchimp_path}")

    # grep a sample SNP
    for i, snpchimp in enumerate(read_snpChimp(snpchimp_path)):
        # get a variant from database
        variant = VariantSheep.objects.get(name=snpchimp.snp_name)

        # read location from SnpChimp data
        location = Location(
            ss_id=snpchimp.ss,
            version="Oar_v3.1",
            chrom=snpchimp.chromosome,
            position=snpchimp.position,
            illumina_top=snpchimp.alleles_a_b_top,
            illumina_forward=snpchimp.alleles_a_b_forward,
            ilmnstrand=snpchimp.orient,
            strand=snpchimp.strand,
            alleles=snpchimp.alleles,
            imported_from="SNPchiMp v.3"
        )

        # update variant with snpchimp data
        variant.rs_id = snpchimp.rs
        variant.locations.append(location)
        variant.save()

    logger.info("Completed")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    main()
