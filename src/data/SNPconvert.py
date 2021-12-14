#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 13:55:46 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import click
import logging
import subprocess

from pathlib import Path
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

from src.features.smarterdb import Dataset, global_connection
from src.features.plinkio import TextPlinkIO
from src.data.common import WORKING_ASSEMBLIES, PLINK_SPECIES_OPT

# Get an instance of a logger
logger = logging.getLogger(__name__)


class CustomTextPlinkIO(TextPlinkIO):
    def _process_pedline(
            self,
            line: list,
            dataset: Dataset,
            coding: str,
            create_samples: bool = False,
            sample_field: str = "original_id"):

        self._check_file_sizes(line)

        logger.debug(f"Processing {line[:10]+ ['...']}")

        # a new line obj
        new_line = line.copy()

        # check and fix genotypes if necessary
        new_line = self._process_genotypes(new_line, coding)

        # need to remove filtered snps from ped line
        for index in sorted(self.filtered, reverse=True):
            # index is snp position. Need to delete two fields
            del new_line[6+index*2+1]
            del new_line[6+index*2]

        return new_line


def get_output_files(prefix: str, working_dir: Path, assembly: str):
    # create output directory
    output_dir = working_dir / assembly
    output_dir.mkdir(exist_ok=True)

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

    working_dir = Path(mapfile).parent

    # instantiating a TextPlinkIO object
    plinkio = CustomTextPlinkIO(
        mapfile=mapfile,
        pedfile=pedfile,
        species=species
    )

    # determine output files
    output_dir, output_map, output_ped = get_output_files(
        file_, working_dir, assembly)

    return plinkio, output_dir, output_map, output_ped


@click.command()
@optgroup.group(
    'Plink input parameters',
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option('--file', 'file_', type=str)
@optgroup.option('--bfile', type=str)
@click.option(
    '--coding',
    type=click.Choice(
        ['top', 'forward'],
        case_sensitive=False),
    default="top", show_default=True,
    help="Illumina coding format"
)
@click.option('--assembly', type=str, required=True)
@click.option('--species', type=str, required=True)
@click.option('--results_dir', type=str, required=True)
def main(file_, bfile, coding, assembly, species, results_dir):
    logger.info(f"{Path(__file__).name} started")

    # find assembly configuration
    if assembly not in WORKING_ASSEMBLIES:
        raise Exception(f"assembly {assembly} not managed by smarter")

    assembly_conf = WORKING_ASSEMBLIES[assembly]

    if file_:
        plinkio, output_dir, output_map, output_ped = deal_with_text_plink(
            file_, assembly, species)

    elif bfile:
        raise NotImplementedError("Plink binary files not yet supported")

    # ok check for results dir
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # define final filename
    final_prefix = results_dir / output_ped.stem

    # if I arrive here, I can create output files

    # read mapdata and read updated coordinates from db
    plinkio.read_mapfile()

    # fetch coordinates relying assembly configuration
    plinkio.fetch_coordinates(
        version=assembly_conf.version,
        imported_from=assembly_conf.imported_from
    )

    logger.info("Writing a new map file with updated coordinates")
    plinkio.update_mapfile(str(output_map))

    logger.info("Writing a new ped file with fixed genotype")
    plinkio.update_pedfile(output_ped, None, coding, create_samples=False)

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
