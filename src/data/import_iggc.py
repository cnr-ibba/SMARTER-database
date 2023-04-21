#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 15:01:13 2023

@author: Paolo Cozzi <bunop@libero.it>

Import data from International Goat Genome Consortium metadata files
"""

import csv
import click
import logging

from pathlib import Path
from collections import namedtuple
from dateutil.parser import parse as parse_date

from src.features.smarterdb import (
    global_connection, Location, VariantGoat)
from src.features.utils import text_or_gzip_open, sanitize
from src.features.illumina import IlluSNP
from src.data.common import update_location, update_rs_id


logger = logging.getLogger(__name__)


def check_strand(strand):
    if strand == '+':
        return "forward"
    elif strand == '-':
        return "reverse"
    else:
        raise NotImplementedError(f"Strand {strand} not managed")


@click.command()
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
    default="locus_name",
    help="Entry name column in datafile (the SNP name)",
    show_default=True,
)
@click.option(
    '--chrom_column',
    type=str,
    help="Chromosome column in datafile",
    required=True,
)
@click.option(
    '--pos_column',
    type=str,
    help="Position column in datafile",
    required=True,
)
@click.option(
    '--strand_column',
    type=str,
    help="Strand column in datafile",
    required=True,
)
@click.option(
    '--sequence_column',
    type=str,
    default="sequence",
    help="Sequence column in datafile",
    show_default=True,
)
@click.option(
    '--rs_column',
    type=str,
    default="rs_",
    help="rsID column in datafile",
    show_default=True,
)
def main(datafile, version, force_update, date, entry_column, chrom_column,
         pos_column, strand_column, sequence_column, rs_column):
    """Read data from Goat genome project and add a new location type
    for variants"""

    logger.info(f"{Path(__file__).name} started")

    if date:
        date = parse_date(date)

    with text_or_gzip_open(datafile) as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader)
        header = [sanitize(col) for col in header]
        Record = namedtuple("Record", header)

        for i, line in enumerate(reader):
            # fix position columns
            try:
                idx = header.index(pos_column)
                line[idx] = int(line[idx])

            except ValueError:
                logger.warning(
                    f"Ignoring '{pos_column}' '{line[idx]}': not integer")

            # make a record from csv line
            record = Record._make(line)

            logger.info(f"Processing {record}")

            # get a variant
            variant = VariantGoat.objects.get(
                name=getattr(record, entry_column))

            logger.debug(f"Got variant {variant}")

            # define an illumina snp from sequence
            illusnp = IlluSNP(
                sequence=getattr(record, sequence_column), max_iter=25)

            logger.debug(f"Got SNP {illusnp}")

            # create a location from input data
            location = Location(
                version=version,
                chrom=getattr(record, chrom_column),
                position=getattr(record, pos_column),
                alleles=illusnp.alleles,
                strand=check_strand(getattr(record, strand_column)),
                illumina=illusnp.illumina,
                illumina_strand=illusnp.strand,
                imported_from="consortium",
                date=date,
            )

            logger.debug(f"Got Location {location}")

            # Should I update a location or not?
            update_variant = False

            variant, updated = update_location(location, variant, force_update)

            if updated:
                update_variant = True

            if getattr(record, rs_column):
                variant, updated = update_rs_id(
                    # create a fake variant with rs_id to use this method
                    VariantGoat(rs_id=[getattr(record, rs_column)]),
                    variant)

                if updated:
                    update_variant = True

            if update_variant:
                # update variant with consortium data
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
