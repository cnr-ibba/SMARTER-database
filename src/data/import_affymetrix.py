#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 15:44:58 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re
import click
import logging

from mongoengine.queryset import Q

from src.features.illumina import IlluSNP, IlluSNPException
from src.features.smarterdb import (
    global_connection, SupportedChip, Location, Probeset, SmarterDBException)
from src.features.affymetrix import read_Manifest
from src.data.common import get_variant_species, update_variant, new_variant

logger = logging.getLogger(__name__)


def get_alleles(record):
    """Define dbSNP alleles from affymetrix record"""

    alleles = None

    if hasattr(record, "ref_allele") and hasattr(record, "alt_allele"):
        # A snp not in dbSNP could have no allele
        if record.ref_allele and record.alt_allele:
            # in dbSNP alleles order has no meaning: it's writtein in
            # alphabetical order
            # https://www.ncbi.nlm.nih.gov/books/NBK44476/#Reports.does_the_order_of_the_alleles_li
            alleles = sorted([record.ref_allele, record.alt_allele])
            alleles = "/".join(alleles)

    return alleles


def fix_illumina_args(record):
    tmp = record.cust_id.split("_")

    args = {}

    # last element is a number
    try:
        tmp[-1] = str(int(tmp[-1]))

        # recode the illumina name and define a re.pattern
        args["name"] = "_".join(tmp[:-1]) + "." + tmp[-1]

    except ValueError as exc:
        logger.debug(
            f"Attempt to convert {tmp[-1]} as integer failed: "
            f"{exc}"
        )

        args["name"] = re.compile(".".join(tmp))

    logger.debug(f"Try to search with {args}")

    return args


def search_database(record, VariantSpecie):
    # if I have a cust_id, search with it
    if record.cust_id:
        # search for cust_id or affy_snp_id
        # (private Affy SNP with unmatched cust_id)
        qs = VariantSpecie.objects.filter(
            Q(name=record.cust_id) | Q(affy_snp_id=record.affy_snp_id))

        if qs.count() == 0:
            logger.debug(f"Can't find a Variant using {record.cust_id}")

            args = fix_illumina_args(record)
            qs = VariantSpecie.objects.filter(**args)

            if qs.count() == 0:
                logger.debug(f"Can't find a Variant using {args}")

    else:
        # search by affy id
        qs = VariantSpecie.objects.filter(
            Q(name=record.affy_snp_id) | Q(affy_snp_id=record.affy_snp_id))

        if qs.count() == 0:
            logger.debug(f"Can't find a Variant using {record.affy_snp_id}")

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
        # ['probe_set_id', 'affy_snp_id', 'dbsnp_rs_id', 'dbsnp_loctype',
        # 'chromosome', 'physical_position', 'position_end', 'strand',
        # 'chrx_pseudo_autosomal_region_1', 'cytoband', 'flank', 'allele_a',
        # 'allele_b', 'ref_allele', 'alt_allele', 'associated_gene',
        # 'genetic_map', 'microsatellite', 'allele_frequencies',
        # 'heterozygous_allele_frequencies', 'number_of_individuals',
        # 'in_hapmap', 'strand_versus_dbsnp', 'probe_count',
        # 'chrx_pseudo_autosomal_region_2', 'minor_allele',
        # 'minor_allele_frequency', 'omim', 'biomedical',
        # 'annotation_notes', 'ordered_alleles', 'allele_count',
        # 'genome', 'cust_id', 'cust_genes', 'cust_traits', 'date']
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
            chrom=record.chromosome,
            position=record.physical_position,
            affymetrix_ab=affymetrix_ab,
            alleles=alleles,
            strand=record.strand,
            illumina_top=illusnp.snp,
            illumina_strand=illusnp.strand,
            imported_from="affymetrix",
            date=record.date,
        )

        rs_id = None

        if record.dbsnp_rs_id:
            rs_id = [record.dbsnp_rs_id]

        variant = VariantSpecie(
            chip_name=[chip_name],
            rs_id=rs_id,
            probesets=[
                Probeset(
                    chip_name=chip_name,
                    probeset_id=[record.probe_set_id]
                )],
            affy_snp_id=record.affy_snp_id,
            sequence={chip_name: record.flank},
            cust_id=record.cust_id,
        )

        logger.debug(f"Processing location {variant}, {location}")

        qs = search_database(record, VariantSpecie)

        if qs.count() == 1:
            try:
                update_variant(qs, variant, location)

            except SmarterDBException as exc:
                # TODO: remove this exception handling
                logger.warn(f"Error with {variant}: {exc} - ignoring snp")

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
