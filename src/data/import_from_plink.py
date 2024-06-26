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
from click_option_group import (
    optgroup, RequiredMutuallyExclusiveOptionGroup,
    MutuallyExclusiveOptionGroup)

from src.features.plinkio import (
    TextPlinkIO, BinaryPlinkIO, plink_binary_exists)
from src.features.smarterdb import Dataset, global_connection, SupportedChip
from src.data.common import WORKING_ASSEMBLIES, PLINK_SPECIES_OPT, AssemblyConf

logger = logging.getLogger(__name__)


def get_output_files(prefix: str, working_dir: Path, assembly: str):
    # create output directory
    output_dir = working_dir / assembly
    output_dir.mkdir(exist_ok=True)

    # determine map outputfile. get the basename of the prefix
    prefix = Path(prefix)

    # sanitize names
    output_map = f"{prefix.name}_updated.map".replace(" ", "_")
    output_map = output_dir / output_map

    # determine ped outputfile
    output_ped = f"{prefix.name}_updated.ped".replace(" ", "_")
    output_ped = output_dir / output_ped

    return output_dir, output_map, output_ped


def deal_with_text_plink(file_: str, dataset: Dataset, assembly: str):
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
    output_dir, output_map, output_ped = get_output_files(
        file_, working_dir, assembly)

    return plinkio, output_dir, output_map, output_ped


def deal_with_binary_plink(bfile: str, dataset: Dataset, assembly: str):
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
    output_dir, output_map, output_ped = get_output_files(
        bfile, working_dir, assembly)

    return plinkio, output_dir, output_map, output_ped


@click.command()
@optgroup.group(
    'Plink input parameters',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option(
    '--file',
    'file_',
    type=str,
    help="PLINK text file prefix")
@optgroup.option(
    '--bfile',
    type=str,
    help="PLINK binary file prefix")
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
@click.option(
    '--src_coding',
    type=click.Choice(
        ['top', 'forward', 'ab', 'affymetrix', 'illumina'],
        case_sensitive=False),
    default="top", show_default=True,
    help="Genotype source coding format"
)
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
@optgroup.group(
    'Variant Search Type',
    cls=MutuallyExclusiveOptionGroup
)
@optgroup.option(
    '--search_field',
    type=str,
    default="name",
    show_default=True,
    help='search variants using this field')
@optgroup.option(
    '--search_by_positions',
    is_flag=True,
    help='search variants using their positions')
@click.option(
    '--src_version',
    type=str,
    help="Source assembly version")
@click.option(
    '--src_imported_from',
    type=str,
    help="Source assembly imported_from")
@click.option(
    '--ignore_coding_errors',
    is_flag=True,
    help=(
        'set SNP as missing when there are coding errors '
        '(no more CodingException)'))
def main(
        file_, bfile, dataset, src_coding, chip_name, assembly,
        create_samples,
        sample_field, search_field, search_by_positions, src_version,
        src_imported_from, ignore_coding_errors):
    """
    Read genotype data from a PLINK file (text or binary) and convert it
    to the desired assembly version using Illumina TOP coding
    """

    logger.info(f"{Path(__file__).name} started")

    # find assembly configuration
    if assembly not in WORKING_ASSEMBLIES:
        raise Exception(f"assembly {assembly} not managed by smarter")

    src_assembly, dst_assembly = None, None

    if src_version and src_imported_from:
        src_assembly = AssemblyConf(src_version, src_imported_from)
        logger.info(f"Got '{src_assembly} as source assembly'")
        dst_assembly = WORKING_ASSEMBLIES[assembly]

    else:
        src_assembly = WORKING_ASSEMBLIES[assembly]

    # get the dataset object
    dataset = Dataset.objects(file=dataset).get()

    logger.debug(f"Found {dataset}")

    if file_:
        plinkio, output_dir, output_map, output_ped = deal_with_text_plink(
            file_, dataset, assembly)

    elif bfile:
        plinkio, output_dir, output_map, output_ped = deal_with_binary_plink(
            bfile, dataset, assembly)

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
    plinkio.read_mapfile()

    if search_by_positions:
        # fetch variants relying positions
        plinkio.fetch_coordinates_by_positions(
            src_assembly=src_assembly,
            dst_assembly=dst_assembly
        )

    else:
        # fetch coordinates relying assembly configuration
        plinkio.fetch_coordinates(
            src_assembly=src_assembly,
            dst_assembly=dst_assembly,
            search_field=search_field,
            chip_name=illumina_chip.name
        )

    logger.info("Writing a new map file with updated coordinates")
    plinkio.update_mapfile(str(output_map))

    logger.info("Writing a new ped file with fixed genotype")
    plinkio.update_pedfile(
        outputfile=output_ped,
        dataset=dataset,
        src_coding=src_coding,
        create_samples=create_samples,
        sample_field=sample_field,
        ignore_coding_errors=ignore_coding_errors
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
