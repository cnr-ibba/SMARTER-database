#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 16:39:57 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import logging
import collections
import datetime

from typing import Union
from dateutil.parser import parse as parse_date

from src.features.utils import sanitize, text_or_gzip_open

# Get an instance of a logger
logger = logging.getLogger(__name__)


def skip_comments(handle) -> (int, list):
    """Ignore comments lines"""

    # track skipped lines
    skipped = list()

    # read first line
    line = handle.readline().strip()

    # search for comments in file
    while line[0] == "#":
        logger.warning(f"Skipping: {line}")
        skipped.append(line)
        position = handle.tell()

        # read another line
        line = handle.readline().strip()

    # the position returned is the one before the one I want
    return position, skipped


def search_manifactured_date(header: list) -> Union[datetime.datetime, None]:
    """Grep manifactured date from illumina header

    Args:
        header (list): affymetrix header section
    Returns:
        datetime.datetime: a datetime object
    """

    records = list(
        filter(
            lambda record: record.startswith("#%create_date="),
            header
        )
    )

    date = None

    if records:
        record = records[0].split("=")
        record = record[1].split()
        date = parse_date(record[0])

    return date


def read_Manifest(path: str, delimiter=","):
    with text_or_gzip_open(path) as handle:
        position, skipped = skip_comments(handle)

        # go back to header section
        handle.seek(position)

        # now read csv file
        reader = csv.reader(handle, delimiter=delimiter)

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

            # set null values to items
            record = [col if col != '---' else None for col in record]

            # convert into collection
            record = SnpChip._make(record)
            yield record
