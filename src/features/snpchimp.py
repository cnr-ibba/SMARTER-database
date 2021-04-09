#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 16:42:36 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import logging
import collections

from src.features.utils import text_or_gzip_open

# Get an instance of a logger
logger = logging.getLogger(__name__)


def clean_chrom(chrom: str):
    """Return 0 if chrom is 99 (unmapped for snpchimp)

    Args:
        chrom (str): the (SNPchiMp) chromsome

    Returns:
        str: 0 if chrom == 99 else chrom

    """

    # forcing type (should be string by database constraints)
    if str(chrom) == "99":
        return "0"

    return chrom


def read_snpChimp(path: str, size=2048):
    sniffer = csv.Sniffer()

    with text_or_gzip_open(path) as handle:
        dialect = sniffer.sniff(handle.read(size))
        handle.seek(0)
        reader = csv.reader(handle, dialect=dialect)

        # get header
        header = next(reader)

        # sanitize column names
        header = [column.lower() for column in header]

        logger.info(header)

        # define a datatype for my data
        SnpChimp = collections.namedtuple("SnpChimp", header)

        # add records to data
        for record in reader:
            # forcing data types
            record[header.index('position')] = int(
                record[header.index('position')])

            # transform NULL valies in None
            record = [None if col == 'NULL' else col for col in record]

            # convert into collection
            record = SnpChimp._make(record)
            yield record
