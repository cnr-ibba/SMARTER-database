#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 23 18:01:40 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import click
import logging

from pathlib import Path
from collections import namedtuple
from dateutil.parser import parse as parse_date

from src.features.smarterdb import (
    global_connection, Location, complement, SmarterDBException)
from src.features.utils import text_or_gzip_open
from src.data.common import get_variant_species, update_location

logger = logging.getLogger(__name__)


def check_chromosomes(chrom, species_class):
    if species_class.lower() == "sheep":
        if int(chrom) <= 26:
            return chrom

        elif int(chrom) == 27:
            return "X"

    else:
        raise NotImplementedError(
            f"Specie {species_class} not yet implemenmented")


def check_strand(variant, alleles):
    """Try to determine the illumina_strand relying on database data and
    received alleles"""

    if alleles == variant.illumina_top:
        return "TOP"

    elif complement(alleles) == variant.illumina_top:
        return "BOT"

    else:
        raise SmarterDBException(
            f"Cannot determine an illumina strand for '{alleles}' ({variant})")


@click.command()
@click.option('--species_class', type=str, required=True)
@click.option('--datafile', type=str, required=True)
@click.option('--version', type=str, required=True)
@click.option(
    '--force_update',
    is_flag=True,
    help="Force location update")
@click.option('--date', type=str, help="A date string")
@click.option(
    '--entry_column',
    type=str,
    default="entry",
    help="Entry name column in datafile (the SNP name)",
    show_default=True,
)
@click.option(
    '--chrom_column',
    type=str,
    default="chrom",
    help="Chromosome column in datafile",
    show_default=True,
)
@click.option(
    '--pos_column',
    type=str,
    default="pos",
    help="Position column in datafile",
    show_default=True,
)
@click.option(
    '--alleles_column',
    type=str,
    default="alleles",
    help="Alleles column in datafile",
    show_default=True,
)
def main(species_class, datafile, version, force_update, date,
         entry_column, chrom_column, pos_column, alleles_column):
    """Read data from Goat or Sheep genome project and add a new location type
    for variants"""

    logger.info(f"{Path(__file__).name} started")

    if date:
        date = parse_date(date)

    # determining the proper VariantSpecies class
    VariantSpecie = get_variant_species(species_class)

    with text_or_gzip_open(datafile) as handle:
        reader = csv.reader(handle, delimiter=",")
        header = next(reader)
        Record = namedtuple("Record", header)

        for i, line in enumerate(reader):
            # fix position column
            idx = header.index(pos_column)
            line[idx] = int(line[idx])

            # fix allele format
            idx = header.index(alleles_column)
            line[idx] = "/".join(list(line[idx]))

            # check chromosome number (27?)
            idx = header.index(chrom_column)
            line[idx] = check_chromosomes(line[idx], species_class)

            # add missing data to line if necessary
            if len(line) < len(header):
                for i in range(len(line), len(header)):
                    line.append(None)

            # make a record from csv line
            record = Record._make(line)

            # get a variant
            variant = VariantSpecie.objects.get(
                name=getattr(record, entry_column))

            # try to determine illumina_strand
            illumina_strand = check_strand(
                variant,
                getattr(record, alleles_column))

            # create a location from input data
            location = Location(
                version=version,
                chrom=getattr(record, chrom_column),
                position=getattr(record, pos_column),
                illumina=getattr(record, alleles_column),
                illumina_strand=illumina_strand,
                imported_from="consortium",
                date=date,
            )

            # Should I update a location or not?
            variant, updated = update_location(
                location, variant, force_update)

            if updated:
                # update variant with snpchimp data
                variant.save()

            if (i+1) % 5000 == 0:
                logger.info(f"{i+1} variants processed")

    logger.info(f"{i+1} variants processed")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
