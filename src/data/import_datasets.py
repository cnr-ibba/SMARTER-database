#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 18:32:54 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import json
import click
import logging
import collections

from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from src.features.smarterdb import global_connection, Dataset
from src.features.utils import sanitize


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
@click.option(
    '--types', nargs=2, type=str, required=True,
    help=(
        '2 argument types (ex. genotypes background, phenotypes foreground,'
        ' etc)'))
def main(input_filepath, output_filepath, types):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """

    logger = logging.getLogger(__name__)

    # connect to database
    global_connection()

    with open(input_filepath) as handle:
        reader = csv.reader(handle, delimiter=";")

        header = next(reader)

        # remove header id
        del(header[0])

        # sanitize column
        header = [sanitize(col) for col in header]

        logger.info("Got %s as header" % header)

        # define a datatype for my data
        Record = collections.namedtuple("Record", header)

        for line in reader:
            # remove id from record
            del(line[0])

            # remove empty string
            line = [col if col != '' else None for col in line]

            record = Record._make(line)
            logger.debug(record)

            # insert or update with a mongodb method
            Dataset.objects(file=record.file).upsert_one(
                **record._asdict(),
                type_=types)

    with open(output_filepath, "w") as handle:
        # after insert collect all data of the same type
        handle.write(Dataset.objects.to_json(indent=2))

    logger.info(f"Data written into database and in {output_filepath}")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
