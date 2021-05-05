#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 17:15:26 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re
import csv
import logging
import collections

from src.features.utils import sanitize, text_or_gzip_open

# Get an instance of a logger
logger = logging.getLogger(__name__)


def skip_lines(handle, skip):
    logger.info(f"Skipping {skip} lines")

    for i in range(skip):
        line = handle.readline().strip()
        position = handle.tell()

        logger.warning(f"Skipping: {line}")

    return position


def skip_until_section(handle, section) -> int:
    """Ignore lines until a precise sections"""

    # search for 'section' record
    while True:
        line = handle.readline().strip()
        position = handle.tell()

        if section in line:
            break

        logger.warning(f"Skipping: {line}")

    return position


def sniff_file(handle, size, position=0):
    sniffer = csv.Sniffer()

    # try to determine dialect
    try:
        data = handle.read(size)
        dialect = sniffer.sniff(data)

    except csv.Error as e:
        logger.error(e)
        logger.error(data)
        raise e

    handle.seek(position)
    return csv.reader(handle, dialect=dialect)


def read_snpMap(path: str, size=2048, skip=0, delimiter=None):
    with open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)

        else:
            if skip > 0:
                skip_lines(handle, skip)

            # try to determine dialect
            reader = sniff_file(handle, size)

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


# TODO: rename this to read_Manifest?
def read_snpChip(path: str, size=2048, skip=0, delimiter=None):
    with text_or_gzip_open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)
            skip_until_section(handle, "[Assay]")

        else:
            if skip > 0:
                position = skip_lines(handle, skip)

            else:
                # search for [Assay] row
                position = skip_until_section(handle, "[Assay]")

            # try to determine dialect
            reader = sniff_file(handle, size, position)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        logger.info(header)

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

            # drop brakets from SNP [A/G] -> A/G
            record[header.index('snp')] = re.sub(
                r'[\[\]]',
                "",
                record[header.index('snp')])

            # convert into collection
            record = SnpChip._make(record)
            yield record


def read_snpList(path: str, size=2048, skip=0, delimiter=None):
    with text_or_gzip_open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)

        else:
            if skip > 0:
                skip_lines(handle, skip)

            # try to determine dialect
            reader = sniff_file(handle, size)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        logger.info(header)

        # define a datatype for my data
        SnpList = collections.namedtuple("SnpList", header)

        # add records to data
        for record in reader:
            # forcing data types
            record[header.index('index')] = int(
                record[header.index('index')])

            record[header.index('position')] = int(
                record[header.index('position')])

            # drop brakets from SNP [A/G] -> A/G
            record[header.index('snp')] = re.sub(
                r'[\[\]]',
                "",
                record[header.index('snp')])

            # convert into collection
            record = SnpList._make(record)
            yield record


def read_illuminaRow(path: str, size=2048):
    with text_or_gzip_open(path) as handle:
        # search for [DATA] record
        position = skip_until_section(handle, "[Data]")

        # try to determine dialect
        reader = sniff_file(handle, size, position)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        # define a datatype for my data
        IlluminaRow = collections.namedtuple("IlluminaRow", header)

        # add records to data
        for record in reader:
            # convert into collection
            record = IlluminaRow._make(record)
            yield record
