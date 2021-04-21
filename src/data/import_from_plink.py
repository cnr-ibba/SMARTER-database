#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 10:36:56 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

This script will upload data into smarter database starting from a couple of
MAP/PED (plink) files and the archive file used for the dataset upload in the
smarter database. Dataset country and species are mandatory and need to be
correctly defined, breed also must be loaded in database in order to define
the full smarter id like CO(untry)SP(ecies)-BREED-ID
The default format is illumina top, but its possible to convert into it
from an illumina forward format
"""

import click
import logging
import subprocess

from pathlib import Path
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

from src.features.plinkio import TextPlinkIO, BinaryPlinkIO
from src.features.smarterdb import Dataset, global_connection

logger = logging.getLogger(__name__)


def get_output_files(prefix, working_dir):
    # create output directory
    output_dir = working_dir / "OARV3"
    output_dir.mkdir(exist_ok=True)

    # determine map outputfile
    output_map = f"{prefix}_updated.map"
    output_map = output_dir / output_map

    # determine ped outputfile
    output_ped = f"{prefix}_updated.ped"
    output_ped = output_dir / output_ped

    return output_dir, output_map, output_ped


def deal_with_text_plink(file_, dataset):
    mapfile = file_ + ".map"
    pedfile = file_ + ".ped"

    # check files are in dataset
    if mapfile not in dataset.contents or pedfile not in dataset.contents:
        raise Exception(
            "Couldn't find files in dataset: check for both "
            f"'{mapfile}' and '{pedfile}' in '{dataset}'")

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        raise Exception(f"Could find dataset directory {working_dir}")

    # determine full file paths
    mappath = working_dir / mapfile
    pedpath = working_dir / pedfile

    # instantiating a TextPlinkIO object
    plinkio = TextPlinkIO(
        mapfile=str(mappath),
        pedfile=str(pedpath),
        species=dataset.species
    )

    # determine output files
    output_dir, output_map, output_ped = get_output_files(file_, working_dir)

    return plinkio, output_dir, output_map, output_ped


def deal_with_binary_plink(bfile, dataset):
    bedfile = bfile + ".bed"
    bimfile = bfile + ".bim"
    famfile = bfile + ".fam"

    all_files = set([bedfile, bimfile, famfile])

    if not all_files.issubset(set(dataset.contents)):
        raise Exception(
            "Couldn't find files in dataset: check for "
            f"'{all_files}' in '{dataset}'")

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        raise Exception(f"Could find dataset directory {working_dir}")

    # determine full file paths
    bfilepath = working_dir / bfile

    # instantiating a BinaryPlinkIO object
    plinkio = BinaryPlinkIO(
        prefix=str(bfilepath),
        species=dataset.species
    )

    # determine output files
    output_dir, output_map, output_ped = get_output_files(bfile, working_dir)

    return plinkio, output_dir, output_map, output_ped


@click.command()
@optgroup.group(
    'Plink input parameters',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option('--file', 'file_', type=str)
@optgroup.option('--bfile', type=str)
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
@click.option(
    '--coding',
    type=click.Choice(
        ['top', 'forward'],
        case_sensitive=False),
    default="top", show_default=True,
    help="Illumina coding format"
)
def main(file_, bfile, dataset, coding):
    """Read sample names from map/ped files and updata smarter database (insert
    a record if necessary and define a smarter id for each sample)
    """

    logger.info(f"{Path(__file__).name} started")

    # get the dataset object
    dataset = Dataset.objects(file=dataset).get()

    logger.debug(f"Found {dataset}")

    if file_:
        plinkio, output_dir, output_map, output_ped = deal_with_text_plink(
            file_, dataset)

    elif bfile:
        plinkio, output_dir, output_map, output_ped = deal_with_binary_plink(
            bfile, dataset)

    # read mapdata and read updated coordinates from db
    plinkio.read_mapfile()
    plinkio.fetch_coordinates(version="Oar_v3.1")

    logger.info("Writing a new map file with updated coordinates")
    plinkio.update_mapfile(str(output_map))

    logger.info("Writing a new ped file with fixed genotype")
    plinkio.update_pedfile(output_ped, dataset, coding)

    # ok check for results dir
    results_dir = dataset.result_dir
    results_dir = results_dir / "OARV3"
    results_dir.mkdir(parents=True, exist_ok=True)

    # ok time to convert data in plink binary format
    cmd = [
        "plink",
        f"--{dataset.species.lower()}",
        "--file",
        f"{output_dir / output_ped.stem}",
        "--make-bed",
        "--out",
        f"{results_dir / output_ped.stem}"
    ]

    # debug
    logger.info("Executing: " + " ".join(cmd))

    subprocess.run(cmd, check=True)

    logger.info(f"{Path(__file__).name} ended")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # connect to database
    global_connection()

    main()
