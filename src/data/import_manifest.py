#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 10:38:05 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import logging

from pathlib import Path
from mongoengine.errors import NotUniqueError

from src.features.illumina import read_snpChip
from src.features.smarterdb import VariantSheep, Location, global_connection


def main():
    logger = logging.getLogger(__name__)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    manifest_file = (
        "data/external/SHE/ILLUMINA/ovinesnp50-genome-assembly-oar-v3-1.csv")
    manifest_path = project_dir / manifest_file

    # connect to database
    global_connection()

    logger.info(f"Reading from {manifest_path}")

    # grep a sample SNP
    for i, snpchip in enumerate(read_snpChip(manifest_path)):
        location = Location(
            version="Oar_v3.1",
            chrom=snpchip.chr,
            position=snpchip.mapinfo,
            illumina=snpchip.snp,
            ilmnstrand=snpchip.ilmnstrand,
            strand=snpchip.sourcestrand,
            imported_from="manifest"
        )

        variant = VariantSheep(
            chip_name=["IlluminaOvineSNP50"],
            name=snpchip.name,
            locations=[location],
            sequence=snpchip.sourceseq,
            sender="AGR_BS"
        )

        try:
            variant.save()

        except NotUniqueError as e:
            logger.error(f"line {i}: Cannot insert {snpchip}, reason: {e}")

    logger.info("Completed")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    main()
