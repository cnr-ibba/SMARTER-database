#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 17:15:26 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re
import csv
import datetime
import logging
import collections

from typing import Union
from dateutil.parser import parse as parse_date

from src.features.utils import sanitize, text_or_gzip_open

# Get an instance of a logger
logger = logging.getLogger(__name__)


def skip_lines(handle, skip) -> (int, list):
    logger.info(f"Skipping {skip} lines")

    # track skipped lines
    skipped = list()

    for i in range(skip):
        line = handle.readline().strip()
        position = handle.tell()

        logger.warning(f"Skipping: {line}")
        skipped.append(line)

    return position, skipped


def skip_until_section(handle, section) -> (int, list):
    """Ignore lines until a precise sections"""

    # track skipped lines
    skipped = list()

    # search for 'section' record
    while True:
        line = handle.readline().strip()
        position = handle.tell()

        logger.warning(f"Skipping: {line}")
        skipped.append(line)

        # last skipped line is included in skipped array
        if section in line:
            break

    return position, skipped


def search_manifactured_date(header: list) -> Union[datetime.datetime, None]:
    """Grep manifactured date from illumina header

    Args:
        header (list): the illumina header skipped lines
    Returns:
        datetime.datetime: a datetime object
    """

    records = list(filter(lambda record: 'date' in record.lower(), header))

    date = None

    if records:
        record = records[0].split(",")
        date = parse_date(record[1])

    return date


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


def read_Manifest(path: str, size=2048, skip=0, delimiter=None):
    with text_or_gzip_open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)
            _, skipped = skip_until_section(handle, "[Assay]")

        else:
            if skip > 0:
                position, skipped = skip_lines(handle, skip)

            else:
                # search for [Assay] row
                position, skipped = skip_until_section(handle, "[Assay]")

            # try to determine dialect
            reader = sniff_file(handle, size, position)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        # ok try to get the manifatcured date
        date = search_manifactured_date(skipped)

        # add date to header
        header.append("date")

        logger.info(header)

        # define a datatype for my data
        SnpChip = collections.namedtuple("SnpChip", header)

        # add records to data
        for record in reader:
            # add date to record
            record.append(date)

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
        position, _ = skip_until_section(handle, "[Data]")

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
