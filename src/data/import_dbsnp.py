#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 18:07:13 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Load data from dbSNP dump files and update illumina SNPs
"""

import click
import logging

from typing import Union
from functools import partial

from src.features.smarterdb import (
    global_connection, SupportedChip, Location, VariantSheep, VariantGoat)
from src.features.dbsnp import read_dbSNP, search_chip_snps
from src.features.illumina import IlluSNP
from src.data.common import (
    get_variant_species, update_location, update_rs_id)

logger = logging.getLogger(__name__)


def search_variant(
        sss: dict,
        rs_id: str,
        locSnpIds: set[str],
        VariantSpecie: Union[VariantSheep, VariantGoat]) -> list[
            Union[VariantSheep, VariantGoat]]:
    """
    Return VariantSheep or VariantGoat instance for the provided SS
    evidences

    Parameters
    ----------
    sss : dict
        A dictionary with all the dbSNP SS hits for illuminas.
    rs_id : str
        The rsId identifier of such SNP.
    locSnpIds : set[str]
        A list of Illumina probe names.
    VariantSpecie : Union[VariantSheep, VariantGoat]
        The specie class (VariantSheep or VariantGoat) to be used when
        searching in SMARTER database

    Returns
    -------
    list[Union[VariantSheep, VariantGoat]]
        A list of variants (Sheep Or Goat).
    """

    if len(sss) > 1:
        logger.warning(f"More than 1 ss found for '{rs_id}'")
        variants = VariantSpecie.objects.filter(name__in=list(locSnpIds))

    elif len(sss) == 1:
        ss = sss[0]

        # ok get a variant from database and return it
        variants = VariantSpecie.objects.filter(name=ss['locSnpId'])

    if len(variants) > 1:
        logger.warning(
            f"Got {len(variants)} Variants for '{rs_id}'")

    return variants


def process_variant(
        snp: dict,
        variant: Union[VariantSheep, VariantGoat],
        supported_chips: list) -> Location:
    """
    Process a SNP read from dbSNP XML file and return a new Location object

    Parameters
    ----------
    snp : dict
        A dictionary with all data from a dbSNP rsId.
    variant : Union[VariantSheep, VariantGoat]
        A SMARTER variant object.
    supported_chips : list
        A list of supported chips as string.

    Returns
    -------
    Location
        A SMARTER Location object for the read SNP.

    """
    logger.debug(f"Processing '{variant.name}'")

    # get the SS relying on ss[locSnpId']
    ss = next(filter(lambda ss: ss['locSnpId'] == variant.name, snp['ss']))

    logger.debug(f"Got {ss} as ss data")

    assembly = snp.get('assembly')

    logger.debug(f"Got {assembly} as assembly")

    # next: I need to determine the illumina top for this SNP
    for chip_name in supported_chips:
        if chip_name in variant.sequence:
            sequence = variant.sequence[chip_name]
            break

    illu_snp = IlluSNP(sequence=sequence, max_iter=25)

    chromosome = "0"
    position = 0

    if (assembly and
            'chromosome' in assembly['component'] and
            assembly['snpstat']['mapWeight'] == 'unique-in-contig'):

        # read chromosome and position
        chromosome = assembly['component']['chromosome']
        position = int(assembly['component']['maploc']['physMapInt'])+1

    # create a new location object
    return Location(
        ss_id=f"ss{ss['ssId']}",
        version=assembly['groupLabel'],
        imported_from=f"dbSNP{assembly['dbSnpBuild']}",
        chrom=chromosome,
        position=position,
        alleles=ss['observed'],
        illumina_strand=ss.get('strand', illu_snp.strand),
        strand=ss.get('orient'),
        illumina=illu_snp.illumina
    )


@click.command()
@click.option(
    '--species_class',
    type=str,
    required=True,
    help="The generic species of dbSNP data (Sheep or Goat)"
    )
@click.option(
    '--input',
    'input_file',
    type=click.Path(exists=True),
    required=True,
    help="The dbSNP input (XML) file"
    )
@click.option(
    '--sender',
    type=str,
    required=True,
    help="The SNP sender (ex. AGR_BS, IGGC)"
    )
def main(species_class, input_file, sender):
    # determining the proper VariantSpecies class
    VariantSpecie = get_variant_species(species_class)

    logger.info("Search all snp names in database")

    # determine the supported chips names
    supported_chips = SupportedChip.objects.filter(
        manifacturer="illumina",
        species=species_class.capitalize(),
    )
    supported_chips = [chip.name for chip in supported_chips]

    logger.debug(f"Considering '{supported_chips}' chips")

    all_snp_names = set([
        variant.name for variant in VariantSpecie.objects.filter(
            chip_name__in=supported_chips).fields(name=1)
    ])

    logger.info(f"Reading from {input_file}")

    handle_filter = partial(search_chip_snps, handle=sender)

    # cicle amoung dbsnp object
    for i, snp in enumerate(filter(handle_filter, read_dbSNP(input_file))):
        # determine rs_id once
        rs_id = f"rs{snp['rsId']}"

        # now get only the SS objects with the required handle
        sss = list(filter(lambda ss: ss['handle'] == sender, snp['ss']))

        # test for locSnpId in my database
        locSnpIds = set([ss['locSnpId'] for ss in sss])

        # Skip variants not in database
        if not locSnpIds.intersection(all_snp_names):
            logger.debug(f"Skipping '{locSnpIds}': not in database")
            continue

        variants = search_variant(sss, rs_id, locSnpIds, VariantSpecie)

        for variant in variants:
            location = process_variant(snp, variant, supported_chips)

            # Should I update a location or not?
            update_variant = False

            variant, updated = update_location(location, variant)

            if updated:
                update_variant = True

            variant, updated = update_rs_id(
                # create a fake variant with rs_id to use this method
                VariantSpecie(rs_id=[rs_id]),
                variant)

            if updated:
                update_variant = True

            if update_variant:
                # update variant with snpchimp data
                variant.save()

        if (i+1) % 5000 == 0:
            logger.info(f"{i+1} variants processed")

    logger.info("Completed")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logging.getLogger('src.features.dbsnp').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)

    # connect to database
    global_connection()

    main()
