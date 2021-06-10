#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 16:39:57 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import sqlite3
import logging
import collections
import datetime

from typing import Union
from dateutil.parser import parse as parse_date

from src.features.utils import sanitize

# Get an instance of a logger
logger = logging.getLogger(__name__)


def search_manifactured_date(
        curs: sqlite3.Cursor) -> Union[datetime.datetime, None]:
    """Grep manifactured date from illumina header

    Args:
        conn (sqlite3.Cursor): a opened cursor to an affymetrix database
    Returns:
        datetime.datetime: a datetime object
    """

    curs.execute(
        "SELECT * FROM Information WHERE key LIKE :key",
        {"key": "create_date"}
    )
    result = curs.fetchone()

    date = None

    if result:
        date = parse_date(result[1])

    return date


def read_Manifest(path: str):
    """Read manifest sqlite file"""

    with sqlite3.connect(path) as conn:
        curs = conn.cursor()

        # ok try to get the manifatcured date
        date = search_manifactured_date(curs)

        statement = """
            SELECT ProbeSet_ID,
                   Affy_SNP_ID,
                   Chr_id,
                   Start,
                   Stop,
                   Strand,
                   dbSNP_RS_ID,
                   Strand_Vs_dbSNP,
                   Flank,
                   Allele_A,
                   Allele_B,
                   Ref_Allele,
                   Alt_Allele,
                   Ordered_Alleles,
                   Genome,
                   cust_id
              FROM Annotations
        """

        reader = curs.execute(statement)

        header = [sanitize(column[0]) for column in reader.description]

        # add date to header
        header.append("date")

        logger.info(header)

        # define a datatype for my data
        SnpChip = collections.namedtuple("SnpChip", header)

        # add records to data
        for record in reader:
            # convert a tutple into list
            record = list(record)

            # add date to record
            record.append(date)
            # convert into collection
            record = SnpChip._make(record)
            yield record
