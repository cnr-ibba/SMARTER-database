#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 17:15:26 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re
import csv
import logging
import itertools
import collections

# Get an instance of a logger
logger = logging.getLogger(__name__)


def sanitize(word):
    # remove spaces from column name and lowercase all
    return re.sub(r"\s+", "_", word).lower()


def read_snpMap(path: str, size=2048):
    sniffer = csv.Sniffer()

    with open(path) as handle:
        dialect = sniffer.sniff(handle.read(size))
        handle.seek(0)
        reader = csv.reader(handle, dialect=dialect)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        # define a datatype for my data
        SnpMap = collections.namedtuple("SnpMap", header)

        # add records to data
        for record in reader:
            # forcing data types
            record[header.index('index')] = int(
                record[header.index('index')])

            record[header.index('position')] = int(
                record[header.index('position')])

            record[header.index('gentrain_score')] = float(
                record[header.index('gentrain_score')])

            record[header.index('normid')] = int(
                record[header.index('normid')])

            # convert into collection
            record = SnpMap._make(record)
            yield record


def read_snpChip(path: str, size=2048):
    sniffer = csv.Sniffer()

    with open(path) as handle:
        dialect = sniffer.sniff(handle.read(size))
        handle.seek(0)
        reader = csv.reader(handle, dialect=dialect)

        # throw away the first 7 lines from reader
        list(itertools.islice(reader, 7))

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        # define a datatype for my data
        SnpChip = collections.namedtuple("SnpChip", header)

        # add records to data
        for record in reader:
            # break after assay section
            if record[0] == '[Controls]':
                logger.debug("[Assay] section processed")
                break

            # forcing data types
            try:
                record[header.index('mapinfo')] = int(
                    record[header.index('mapinfo')])

            except ValueError as e:
                logging.warning(
                    "Cannot parse %s:%s" % (record, str(e)))

            # convert into collection
            record = SnpChip._make(record)
            yield record
