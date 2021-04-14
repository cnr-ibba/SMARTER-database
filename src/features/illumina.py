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

from src.features.utils import sanitize, text_or_gzip_open

# Get an instance of a logger
logger = logging.getLogger(__name__)


def read_snpMap(path: str, size=2048, skip=0):
    sniffer = csv.Sniffer()

    with open(path) as handle:
        if skip > 0:
            logger.info(f"Skipping {skip} lines")
            tmp = itertools.islice(handle, skip)
            for line in tmp:
                logger.debug(f"Skipping: {line}")

        # try to determine dialect
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


def read_snpChip(path: str, size=2048, skip=0, delimiter=None):
    sniffer = csv.Sniffer()

    with text_or_gzip_open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)

        else:
            # TODO: search for [Assay] row
            if skip > 0:
                logger.info(f"Skipping {skip} lines")
                tmp = itertools.islice(handle, skip)
                for line in tmp:
                    logger.error(f"Skipping: {line}")

            # try to determine dialect
            dialect = sniffer.sniff(handle.read(size))
            handle.seek(0)
            reader = csv.reader(handle, dialect=dialect)

        # throw away the first 7 lines from reader
        list(itertools.islice(reader, 7))

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
    sniffer = csv.Sniffer()

    with text_or_gzip_open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)

        else:
            # TODO: search for [Assay] row
            if skip > 0:
                logger.info(f"Skipping {skip} lines")
                tmp = itertools.islice(handle, skip)
                for line in tmp:
                    logger.error(f"Skipping: {line}")

            # try to determine dialect
            dialect = sniffer.sniff(handle.read(size))
            handle.seek(0)
            reader = csv.reader(handle, dialect=dialect)

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
    sniffer = csv.Sniffer()
    position = 0

    with text_or_gzip_open(path) as handle:
        # search for [DATA] record
        while True:
            line = handle.readline()
            position = handle.tell()
            line = line.strip()

            if line == '[Data]':
                break

            logger.warning(f"Skipping: {line}")

        # try to determine dialect
        dialect = sniffer.sniff(handle.read(size))
        handle.seek(position)
        reader = csv.reader(handle, dialect=dialect)

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
