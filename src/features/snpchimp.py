#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 16:42:36 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import logging
import collections

# Get an instance of a logger
logger = logging.getLogger(__name__)


def read_snpChimp(path: str, size=2048):
    sniffer = csv.Sniffer()

    with open(path) as handle:
        dialect = sniffer.sniff(handle.read(size))
        handle.seek(0)
        reader = csv.reader(handle, dialect=dialect)

        # get header
        header = next(reader)

        # sanitize column names
        header = [column.lower() for column in header]

        # define a datatype for my data
        SnpChimp = collections.namedtuple("SnpChimp", header)

        # add records to data
        for record in reader:
            # forcing data types
            record[header.index('position')] = int(
                record[header.index('position')])

            # convert into collection
            record = SnpChimp._make(record)
            yield record
