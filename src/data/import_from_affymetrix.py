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

from src.features.plinkio import (
    AffyPlinkIO, AffyReportIO, plink_binary_exists)
from src.features.smarterdb import Dataset, global_connection, SupportedChip
from src.data.common import WORKING_ASSEMBLIES, PLINK_SPECIES_OPT, AssemblyConf

logger = logging.getLogger(__name__)


def get_output_files(prefix: str, working_dir: Path, assembly: str):
    # create output directory
    output_dir = working_dir / assembly
    output_dir.mkdir(exist_ok=True)

    # determine map outputfile. get the basename of the prefix
    prefix = Path(prefix)

    output_map = f"{prefix.name}_updated.map".replace(" ", "_")
    output_map = output_dir / output_map

    # determine ped outputfile
    output_ped = f"{prefix.name}_updated.ped".replace(" ", "_")
    output_ped = output_dir / output_ped

    return output_dir, output_map, output_ped


def deal_with_prefix(prefix: str, dataset: Dataset, assembly: str):
    mapfile = prefix + ".map"
    pedfile = prefix + ".ped"

    # check files are in dataset
    if mapfile not in dataset.contents or pedfile not in dataset.contents:
        raise Exception(
            "Couldn't find files in dataset: check for both "
            f"'{mapfile}' and '{pedfile}' in '{dataset}'")

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        raise Exception(f"Couldn't find dataset directory '{working_dir}'")

    # determine full file paths
    mappath = working_dir / mapfile
    pedpath = working_dir / pedfile

    # instantiating a TextPlinkIO object
    plinkio = AffyPlinkIO(
        mapfile=str(mappath),
        pedfile=str(pedpath),
        species=dataset.species
    )

    # determine output files
    output_dir, output_map, output_ped = get_output_files(
        prefix, working_dir, assembly)

    return plinkio, output_dir, output_map, output_ped


def deal_with_report(report: str, dataset: Dataset, assembly: str):
    # check file is in dataset
    if report not in dataset.contents:
        raise Exception(
            "Couldn't find file in dataset: check for "
            f"'{report}' in '{dataset}'")

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        raise Exception(f"Couldn't find dataset directory '{working_dir}'")

    # determine full file paths
    reportpath = working_dir / report

    # instantiating a TextPlinkIO object
    plinkio = AffyReportIO(
        report=reportpath,
        species=dataset.species
    )

    # determine output files
    output_dir, output_map, output_ped = get_output_files(
        Path(report).stem, working_dir, assembly)

    return plinkio, output_dir, output_map, output_ped


@click.command()
@optgroup.group(
    'Affymetrix input files',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option(
    '--prefix',
    type=str,
    help="File prefix for map and ped files (like plink does)")
@optgroup.option(
    '--report',
    type=str,
    help="Affymetrix report path")
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
@click.option(
    '--src_coding',
    type=click.Choice(
        ['ab', 'affymetrix'],
        case_sensitive=False),
    default="affymetrix", show_default=True,
    help="Affymetrix source coding format"
)
@click.option(
    '--breed_code',
    type=str,
    help="A breed code to be assigned on all samples while creating samples")
@click.option(
    '--chip_name',
    type=str,
    required=True,
    help="The SMARTER SupportedChip name")
@click.option(
    '--assembly',
    type=str,
    required=True,
    help="Destination assembly of the converted genotypes")
@click.option(
    '--create_samples',
    is_flag=True,
    help="Create a new SampleSheep or SampleGoat object if doesn't exist")
@click.option(
    '--sample_field',
    type=str,
    default="original_id",
    help="Search samples using this attribute"
)
@click.option(
    '--search_field',
    type=str,
    default="probeset_id",
    show_default=True,
    help='search variants using this field')
@click.option(
    '--src_version',
    type=str,
    help="Source assembly version",
    required=True)
@click.option(
    '--src_imported_from',
    type=str,
    help="Source assembly imported_from",
    required=True)
@click.option(
    '--max_samples',
    type=int,
    help="Limit import to first samples (only valid for affymetrix report)")
@click.option(
    '--skip_coordinate_check',
    is_flag=True,
    help="Skip coordinate check (only valid for affymetrix report)")
def main(
        prefix, report, dataset, src_coding, breed_code, chip_name, assembly,
        create_samples, sample_field, search_field, src_version,
        src_imported_from, max_samples, skip_coordinate_check):
    """
    Read genotype data from affymetrix files and convert it
    to the desidered assembly version using Illumina TOP coding
    """

    logger.info(f"{Path(__file__).name} started")

    # find assembly configuration
    if assembly not in WORKING_ASSEMBLIES:
        raise Exception(f"assembly {assembly} not managed by smarter")

    # define assemblies
    src_assembly = AssemblyConf(src_version, src_imported_from)
    logger.info(f"Got '{src_assembly} as source assembly'")
    dst_assembly = WORKING_ASSEMBLIES[assembly]

    # get the dataset object
    dataset = Dataset.objects(file=dataset).get()

    logger.debug(f"Found {dataset}")

    if prefix:
        plinkio, output_dir, output_map, output_ped = deal_with_prefix(
            prefix, dataset, assembly)

    elif report:
        plinkio, output_dir, output_map, output_ped = deal_with_report(
            report, dataset, assembly)

    # check chip_name
    illumina_chip = SupportedChip.objects(name=chip_name).get()

    # set chip name for this sample
    plinkio.chip_name = illumina_chip.name

    # test if I have already run this analysis

    # ok check for results dir
    results_dir = dataset.result_dir
    results_dir = results_dir / assembly
    results_dir.mkdir(parents=True, exist_ok=True)

    # define final filename
    final_prefix = results_dir / output_ped.stem

    # test for processed files existance
    if plink_binary_exists(final_prefix):
        logger.warning(f"Skipping {dataset} processing: {final_prefix} exists")
        logger.info(f"{Path(__file__).name} ended")
        return

    # if I arrive here, I can create output files

    # read mapdata and read updated coordinates from db
    if prefix:
        # I have a .map file to read
        plinkio.read_mapfile()

    elif report:
        # this is an affymetrix reportfile
        plinkio.read_reportfile(n_samples=max_samples)

    # fetch coordinates relying assembly configuration. Mind affy probeset_id
    plinkio.fetch_coordinates(
        src_assembly=src_assembly,
        dst_assembly=dst_assembly,
        search_field=search_field,
        chip_name=illumina_chip.name,
        skip_check=skip_coordinate_check
    )

    logger.info("Writing a new map file with updated coordinates")
    plinkio.update_mapfile(str(output_map))

    logger.info("Writing a new ped file with fixed genotype (illumina TOP)")
    plinkio.update_pedfile(
        outputfile=output_ped,
        dataset=dataset,
        src_coding=src_coding,
        breed=breed_code,
        create_samples=create_samples,
        sample_field=sample_field
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
