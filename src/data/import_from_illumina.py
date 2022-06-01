#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 11:56:02 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

This script will import data from illumina row format and the archive file used
while uploading the dataset in the smarter database.
Dataset country and species are mandatory and need to be
correctly defined, breed also must be loaded in database in order to define
the full smarter id like CO(untry)SP(ecies)-BREED-ID
"""

import click
import logging
import subprocess

from pathlib import Path

from src.features.plinkio import IlluminaReportIO, plink_binary_exists
from src.features.smarterdb import global_connection, SupportedChip
from src.data.common import (
    fetch_and_check_dataset, WORKING_ASSEMBLIES, PLINK_SPECIES_OPT)

logger = logging.getLogger(__name__)


def get_output_files(reportpath: str, working_dir: Path, assembly: str):
    # create output directory
    output_dir = working_dir / assembly
    output_dir.mkdir(exist_ok=True)

    # determine map outputfile. get the basename of the prefix
    output_map = Path(reportpath).stem + "_updated.map"
    output_map = output_dir / output_map

    # creating ped file for writing updated genotypes
    output_ped = Path(reportpath).stem + "_updated.ped"
    output_ped = output_dir / output_ped

    return output_dir, output_map, output_ped


@click.command()
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
@click.option('--snpfile', type=str, required=True)
@click.option('--report', type=str, required=True)
@click.option(
    '--coding',
    type=click.Choice(
        ['ab'],
        case_sensitive=False),
    default="ab", show_default=True,
    help="Illumina coding format"
)
@click.option(
    '--breed_code',
    type=str,
    help="Assign this FID to every sample in illumina report")
@click.option('--chip_name', type=str, required=True)
@click.option('--assembly', type=str, required=True)
@click.option('--create_samples', is_flag=True)
def main(
        dataset, snpfile, report, coding, breed_code, chip_name, assembly,
        create_samples):

    logger.info(f"{Path(__file__).name} started")

    # find assembly configuration
    if assembly not in WORKING_ASSEMBLIES:
        raise Exception(f"assembly {assembly} not managed by smarter")

    src_assembly = WORKING_ASSEMBLIES[assembly]

    # custom method to check a dataset and ensure that needed stuff exists
    dataset, [snpfilepath, reportpath] = fetch_and_check_dataset(
        archive=dataset,
        contents=[snpfile, report]
    )

    # check chip_name
    illumina_chip = SupportedChip.objects(name=chip_name).get()

    # instantiating a TextPlinkIO object
    report = IlluminaReportIO(
        snpfile=snpfilepath,
        report=reportpath,
        species=dataset.species,
        chip_name=illumina_chip.name
    )

    # test if I have already run this analysis

    # ok check for results dir
    results_dir = dataset.result_dir
    results_dir = results_dir / assembly
    results_dir.mkdir(parents=True, exist_ok=True)

    output_dir, output_map, output_ped = get_output_files(
        reportpath, dataset.working_dir, assembly)

    # define final filename
    final_prefix = results_dir / output_ped.stem

    # test for processed files existance
    if plink_binary_exists(final_prefix):
        logger.warning(f"Skipping {dataset} processing: {final_prefix} exists")
        logger.info(f"{Path(__file__).name} ended")
        return

    # if I arrive here, I can create output files

    # set mapdata and read updated coordinates from db
    report.read_snpfile()

    # fetch coordinates relying assembly configuration
    report.fetch_coordinates(
        src_assembly=src_assembly
    )

    logger.info("Writing a new map file with updated coordinates")
    report.update_mapfile(str(output_map))

    # creating ped file for writing updated genotypes
    report.update_pedfile(
        output_ped,
        dataset,
        coding,
        fid=breed_code,
        create_samples=create_samples
    )

    # ok time to convert data in plink binary format
    cmd = ["plink"] + PLINK_SPECIES_OPT[dataset.species] + [
        "--file",
        f"{output_dir / output_ped.stem}",
        "--make-bed",
        "--out",
        f"{final_prefix}"
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
