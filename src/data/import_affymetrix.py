#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 15:44:58 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging

from src.features.illumina import IlluSNP
from src.features.smarterdb import global_connection, SupportedChip, Location
from src.features.affymetrix import read_Manifest
from src.data.common import get_variant_species, update_variant, new_variant

logger = logging.getLogger(__name__)


@click.command()
@click.option('--species', type=str, required=True)
@click.option('--manifest', type=str, required=True)
@click.option('--chip_name', type=str, required=True)
@click.option('--version', type=str, required=True)
def main(species, manifest, chip_name, version):
    # determining the proper VariantSpecies class
    VariantSpecie = get_variant_species(species)

    # check chip_name
    affymetrix_chip = SupportedChip.objects(name=chip_name).get()

    # reset chip data (if any)
    affymetrix_chip.n_of_snps = 0

    logger.info(f"Reading from {manifest}")

    # grep a sample SNP
    for i, record in enumerate(read_Manifest(manifest)):
        # update chip data indipendentely if it is an update or not
        affymetrix_chip.n_of_snps += 1

        # ['probeset_id', 'affy_snp_id', 'chr_id', 'start', 'stop', 'strand',
        # 'dbsnp_rs_id', 'strand_vs_dbsnp', 'flank', 'allele_a', 'allele_b',
        # 'ref_allele', 'alt_allele', 'ordered_alleles', 'genome', 'cust_id',
        # 'date']

        logger.debug(f"Processing {record}")

        affymetrix_ab = f"{record.allele_a}/{record.allele_b}"

        alleles = None

        # A snp not in dbSNP could have no allele
        if record.ref_allele and record.alt_allele:
            # in dbSNP alleles order has no meaning: it's writtein in
            # alphabetical order
            # https://www.ncbi.nlm.nih.gov/books/NBK44476/#Reports.does_the_order_of_the_alleles_li
            alleles = sorted([record.ref_allele, record.alt_allele])
            alleles = "/".join(alleles)

        # get the illumina coded snp relying on sequence
        illusnp = IlluSNP(record.flank, max_iter=25).toTop()

        # create a location object
        location = Location(
            version=version,
            chrom=str(record.chr_id),
            position=record.start,
            affymetrix_ab=affymetrix_ab,
            alleles=alleles,
            strand=record.strand,
            illumina_top=illusnp.snp,
            illumina_strand=illusnp.strand,
            imported_from="affymetrix",
            date=record.date,
        )

        variant = VariantSpecie(
            chip_name=[chip_name],
            rs_id=record.dbsnp_rs_id,
            probeset_id=[record.probeset_id],
            affy_snp_id=record.affy_snp_id,
            sequence={'affymetrix': record.flank},
            cust_id=record.cust_id,
        )

        logger.debug(f"Processing location {variant}, {location}")

        # search for a snp in database (relying on name or rs_id)
        if record.dbsnp_rs_id:
            qs = VariantSpecie.objects.filter(rs_id=record.dbsnp_rs_id)

        else:
            qs = VariantSpecie.objects.filter(name=record.affy_snp_id)

        if qs.count() == 1:
            update_variant(qs, variant, location)

        elif qs.count() == 0:
            new_variant(variant, location)

        if (i+1) % 5000 == 0:
            logger.info(f"{i+1} variants processed")

    # update chip info
    affymetrix_chip.save()

    logger.info(f"{i+1} variants processed")

    logger.info("Completed")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
