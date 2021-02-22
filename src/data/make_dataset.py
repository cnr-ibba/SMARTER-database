#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 18:32:54 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import re
import csv
import json
import click
import logging

from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pymongo import MongoClient


# function to convert string to camelCase
def camelCase(string):
    string = re.sub(r"(_|-|\.)+", " ", string).title().replace(" ", "")
    return string[0].lower() + string[1:]


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
    client = MongoClient(
        'mongodb://localhost:27017/',
        username=os.getenv("MONGODB_ROOT_USER"),
        password=os.getenv("MONGODB_ROOT_PASS")
    )

    # get database and collection
    db = client['smarter']
    collection = db['dataset']

    with open(input_filepath) as handle:
        reader = csv.reader(handle, delimiter=";")

        header = next(reader)
        header[0] = 'id'

        # sanitize column
        header = [camelCase(col) for col in header]

        logger.info("Got %s as header" % header)

        for line in reader:
            record = dict()

            # skip the header id column
            for i, col in enumerate(header[1:], 1):
                record[col] = line[i]

            # add type data
            record['type'] = types

            logger.info("Inserting %s" % str(record))

            collection.update_one(
                {"file": record["file"]},
                {"$set": record},
                upsert=True
            )

    with open(output_filepath, "w") as handle:
        # after insert collect all data of the same type
        docs = list(
            collection.find(
                {'type': {'$all': types}},
                {'_id': 0}
            )
        )

        # write a record in json file
        json.dump(docs, handle, indent=2)

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
