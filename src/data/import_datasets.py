#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 18:32:54 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import click
import logging
import zipfile
import collections

from pathlib import Path

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

            # search for the archive file
            archive = next(project_dir.rglob(record.file))
            logger.info(f"Found {archive} as archive")

            archive = zipfile.ZipFile(archive)

            logger.debug("Get file contents")
            contents = archive.namelist()
            logger.debug(contents)

            # insert or update with a mongodb method
            dataset = Dataset.objects(file=record.file).upsert_one(
                **record._asdict(),
                type_=types,
                contents=contents)

            # ok extract content to working directory
            # TODO: don't work with plain text files, try to work with
            # compressed data
            working_dir = project_dir / f"data/interim/{dataset.id}"
            working_dir.mkdir(exist_ok=True)

            for member in contents:
                test = working_dir / member
                if not test.exists():
                    logger.info(f"Extract '{member}': in '{working_dir}'")
                    archive.extract(member, working_dir)

                else:
                    logger.debug(f"Skipping {member}: already extracted")

    with open(output_filepath, "w") as handle:
        # after insert collect all data of the same type
        handle.write(Dataset.objects.to_json(indent=2))

    logger.info(f"Data written into database and in {output_filepath}")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    # this is the root of SMARTER-database project
    project_dir = Path(__file__).resolve().parents[2]

    main()
