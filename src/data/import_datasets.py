#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 18:32:54 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import csv
import sys
import click
import logging
import zipfile
import collections

from pathlib import Path

from src.features.smarterdb import global_connection, Dataset
from src.features.utils import sanitize, get_raw_dir

logger = logging.getLogger(__name__)


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.option(
    '--types', nargs=2, type=str, required=True,
    help=(
        '2 argument types (ex. genotypes background, phenotypes foreground,'
        ' etc)'))
def main(input_filepath, types):
    """
    Import a dataset stored in ``data/raw`` folder into the *smarter*
    database and unpack file contents into ``data/interim`` subfolder

    INPUT_FILEPATH:  The CSV dataset description file
    """

    logger.info(f"{Path(__file__).name} started")

    # where to find raw data in SMARTER-database project
    raw_dir = get_raw_dir()

    with open(input_filepath) as handle:
        reader = csv.reader(handle, delimiter=";")

        header = next(reader)

        # remove header id
        del header[0]

        # sanitize column
        header = [sanitize(col) for col in header]

        logger.debug("Got '%s' as header" % header)

        # define a datatype for my data
        Record = collections.namedtuple("Record", header)

        for line in reader:
            # remove id from record
            del line[0]

            # remove empty values
            line = [col if col != '' else None for col in line]

            record = Record._make(line)
            logger.debug(record)

            # search for the archive file
            try:
                archive = next(raw_dir.rglob(record.file))
                logger.info(f"Found '{archive}' dataset")

            except StopIteration:
                logger.critical(f"Cannot find '{record.file}' in '{raw_dir}'")
                sys.exit(f"'{record.file}' does not exists")

            archive = zipfile.ZipFile(archive)

            logger.debug("Get file contents")
            contents = archive.namelist()
            logger.debug(contents)

            # add or create dataset (file is a unique key)
            qs = Dataset.objects(file=record.file)

            if qs.count() == 0:
                # create a new object
                dataset = Dataset(
                    **record._asdict(),
                    type_=types,
                    contents=contents)

                logger.info(f"Create new dataset '{dataset}'")

            elif qs.count() == 1:
                # update object
                dataset = qs.get()

                for k, v in record._asdict().items():
                    setattr(dataset, k, v)

                dataset.type_ = types
                dataset.contents = contents

                logger.debug(f"Dataset '{dataset}' updated")

            dataset.save()

            # ok extract content to working directory
            # TODO: don't work with plain text files, try to work with
            # compressed data
            working_dir = dataset.working_dir
            working_dir.mkdir(exist_ok=True)

            for member in contents:
                test = working_dir / member
                if not test.exists():
                    logger.info(f"Extract '{member}': in '{working_dir}'")
                    archive.extract(member, working_dir)

                else:
                    logger.debug(f"Skipping '{member}': already extracted")

    logger.info("Data written into database")

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
