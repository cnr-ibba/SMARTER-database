#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 15:44:58 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re
import click
import logging

from src.features.illumina import IlluSNP, IlluSNPException
from src.features.smarterdb import global_connection, SupportedChip, Location
from src.features.affymetrix import read_Manifest
from src.data.common import get_variant_species, update_variant, new_variant

logger = logging.getLogger(__name__)


def get_alleles(record):
    """Define dbSNP alleles from affymetrix record"""

    alleles = None

    # A snp not in dbSNP could have no allele
    if record.ref_allele and record.alt_allele:
        # in dbSNP alleles order has no meaning: it's writtein in
        # alphabetical order
        # https://www.ncbi.nlm.nih.gov/books/NBK44476/#Reports.does_the_order_of_the_alleles_li
        alleles = sorted([record.ref_allele, record.alt_allele])
        alleles = "/".join(alleles)

    return alleles


def search_database(record, VariantSpecie):
    # try to read the cust_id like illumina name:
    illumina_name = None

    if record.cust_id:
        tmp = record.cust_id.split("_")

        # last element is a number
        tmp[-1] = str(int(tmp[-1]))

        # recode the illumina name and define a re.pattern
        illumina_name = "_".join(tmp[:-1]) + "." + tmp[-1]
        illumina_pattern = re.compile(".".join(tmp))

    # search for a snp in database (relying on illumina name first)
    if illumina_name:
        qs = VariantSpecie.objects.filter(name=illumina_name)

        if qs.count() == 0:
            logger.debug(
                f"Couldn't find a variant with '{illumina_name}'. "
                f"Trying with '{illumina_pattern}' pattern")
            # ok make an attempt with pattern
            qs = VariantSpecie.objects.filter(name=illumina_pattern)

    else:
        qs = VariantSpecie.objects.filter(name=record.affy_snp_id)

    return qs


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
        # ['probeset_id', 'affy_snp_id', 'chr_id', 'start', 'stop', 'strand',
        # 'dbsnp_rs_id', 'strand_vs_dbsnp', 'flank', 'allele_a', 'allele_b',
        # 'ref_allele', 'alt_allele', 'ordered_alleles', 'genome', 'cust_id',
        # 'date']
        logger.debug(f"Processing {record}")

        affymetrix_ab = f"{record.allele_a}/{record.allele_b}"

        alleles = get_alleles(record)

        # get the illumina coded snp relying on sequence
        try:
            illusnp = IlluSNP(record.flank, max_iter=25).toTop()

        except IlluSNPException as e:
            logger.debug(e)
            logger.warning(
                f"Ignoring {record}: only 2 allelic SNPs are supported")
            continue

        # update chip data indipendentely if it is an update or not
        affymetrix_chip.n_of_snps += 1

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

        qs = search_database(record, VariantSpecie)

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
