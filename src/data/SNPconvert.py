#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 13:55:46 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging
import tempfile
import subprocess

from pathlib import Path
from click_option_group import (
    optgroup, RequiredMutuallyExclusiveOptionGroup,
    MutuallyExclusiveOptionGroup)

from src.features.smarterdb import (
    Dataset, global_connection, SmarterDBException)
from src.features.plinkio import TextPlinkIO, IlluminaReportIO, BinaryPlinkIO
from src.data.common import WORKING_ASSEMBLIES, PLINK_SPECIES_OPT, AssemblyConf

# Get an instance of a logger
logger = logging.getLogger(__name__)


class CustomMixin():
    def _process_pedline(
            self,
            line: list,
            dataset: Dataset,
            src_coding: str,
            create_sample: bool = False,
            sample_field: str = "original_id",
            ignore_coding_errors: bool = False,
            dst_coding: str = "top"):

        self._check_file_sizes(line)

        logger.debug(f"Processing {line[:10]+ ['...']}")

        # a new line obj
        new_line = line.copy()

        # check and fix genotypes if necessary
        new_line = self._process_genotypes(
            new_line,
            src_coding,
            ignore_coding_errors,
            dst_coding)

        # need to remove filtered snps from ped line
        for index in sorted(self.filtered, reverse=True):
            # index is snp position. Need to delete two fields
            del new_line[6+index*2+1]
            del new_line[6+index*2]

        return new_line


class CustomTextPlinkIO(CustomMixin, TextPlinkIO):
    pass


class CustomBinaryPlinkIO(CustomMixin, BinaryPlinkIO):
    pass


class CustomIlluminaReportIO(CustomMixin, IlluminaReportIO):
    def read_reportfile(
            self, breed="0", dataset: Dataset = None, *args, **kwargs):
        """Custom Open illumina report returns iterator"""

        logger.debug("Custom 'read_reportfile' called")

        return super().read_reportfile(breed, dataset, *args, **kwargs)


def get_output_files(prefix: str, assembly: str):
    # create output directory
    working_dir = tempfile.mkdtemp()
    output_dir = Path(working_dir)

    # determine map outputfile. get the basename of the prefix
    prefix = Path(prefix)

    output_map = f"{prefix.name}_updated.map"
    output_map = output_dir / output_map

    # determine ped outputfile
    output_ped = f"{prefix.name}_updated.ped"
    output_ped = output_dir / output_ped

    return output_dir, output_map, output_ped


def deal_with_text_plink(file_: str, assembly: str, species: str):
    mapfile = file_ + ".map"
    pedfile = file_ + ".ped"

    # instantiating a TextPlinkIO object
    plinkio = CustomTextPlinkIO(
        mapfile=mapfile,
        pedfile=pedfile,
        species=species
    )

    plinkio.read_mapfile()

    # determine output files
    output_dir, output_map, output_ped = get_output_files(file_, assembly)

    return plinkio, output_dir, output_map, output_ped


def deal_with_binary_plink(bfile: str, assembly: str, species: str):
    # instantiating a BinaryPlinkIO object
    plinkio = CustomBinaryPlinkIO(
        prefix=bfile,
        species=species
    )

    plinkio.read_mapfile()

    # determine output files
    output_dir, output_map, output_ped = get_output_files(bfile, assembly)

    return plinkio, output_dir, output_map, output_ped


def deal_with_illumina(
        report: str, snpfile: str, assembly: str, species: str):
    plinkio = CustomIlluminaReportIO(
        snpfile=snpfile,
        report=report,
        species=species,
    )

    plinkio.read_snpfile()

    # determine output files
    output_dir, output_map, output_ped = get_output_files(
        Path(report).stem, assembly)

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
@optgroup.option(
    '--report',
    type=str,
    help="The illumina report file")
@click.option(
    '--snpfile',
    type=str,
    help="The illumina SNPlist file")
@click.option(
    '--src_coding',
    type=click.Choice(
        ['top', 'forward', 'ab'],
        case_sensitive=False),
    default="top", show_default=True,
    help="Illumina source coding format"
)
@click.option(
    '--assembly',
    type=str,
    required=True,
    help="Destination assembly of the converted genotypes")
@click.option(
    '--species',
    type=str,
    required=True,
    help="The SMARTER assembly species (Goat or Sheep)")
@click.option(
    '--results_dir',
    type=str,
    required=True,
    help="Where results will be saved")
@click.option(
    '--chip_name',
    type=str,
    help="The SMARTER SupportedChip name")
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
        file_, bfile, report, snpfile, src_coding, assembly, species,
        chip_name, results_dir, search_field, search_by_positions, src_version,
        src_imported_from, ignore_coding_errors):
    """
    Convert a PLINK/Illumina report file in a SMARTER-like output file, without
    inserting data in SMARTER-database. Useful to convert data relying on
    SMARTER-database for private datasets (data which cannot be included in
    SMARTER-database)
    """

    logger.info(f"{Path(__file__).name} started")

    # find assembly configuration
    if assembly not in WORKING_ASSEMBLIES:
        raise SmarterDBException(
            f"assembly {assembly} not managed by smarter")

    src_assembly, dst_assembly = None, None

    if src_version and src_imported_from:
        src_assembly = AssemblyConf(src_version, src_imported_from)
        logger.info(f"Got '{src_assembly} as source assembly'")
        dst_assembly = WORKING_ASSEMBLIES[assembly]

    else:
        src_assembly = WORKING_ASSEMBLIES[assembly]

    if file_:
        plinkio, output_dir, output_map, output_ped = deal_with_text_plink(
            file_, assembly, species)

    elif bfile:
        plinkio, output_dir, output_map, output_ped = deal_with_binary_plink(
            bfile, assembly, species)

    elif report:
        if not snpfile:
            raise RuntimeError(f"Missing snpfile for report {report}")

        plinkio, output_dir, output_map, output_ped = deal_with_illumina(
            report, snpfile, assembly, species)

    # ok check for results dir
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # define final filename
    final_prefix = results_dir / output_ped.stem

    # if I arrive here, I can create output files

    # fetch coordinates relying assembly configuration
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
            chip_name=chip_name
        )

    logger.info("Writing a new map file with updated coordinates")
    plinkio.update_mapfile(str(output_map))

    logger.info("Writing a new ped file with fixed genotype")
    plinkio.update_pedfile(
        outputfile=output_ped,
        dataset=None,
        src_coding=src_coding,
        create_samples=False,
        ignore_coding_errors=ignore_coding_errors,
        dst_coding="top"
    )

    # ok time to convert data in plink binary format
    cmd = ["plink"] + PLINK_SPECIES_OPT[species] + [
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

    # call main function
    main()
