#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 10:36:56 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

This script will upload data into smarter database starting from a couple of
MAP/PED (plink) files and the archive file used for the dataset upload in the
smarter database. Dataset country and species are mandatory and need to be
correctly define, breed also must be loaded in database in order to define
the full smarter id like CO(untry)SP(ecies)-BREED-ID

"""

import csv
import click
import logging
import itertools
import subprocess

from pathlib import Path
from mongoengine.queryset.visitor import Q
from tqdm import tqdm

from src.features.smarterdb import (
    global_connection, Dataset, Breed, SampleSheep, VariantSheep, Location)
from src.features.utils import TqdmToLogger

logger = logging.getLogger(__name__)


def is_top(genotype: list, location: Location, missing: str = "0") -> bool:
    """Return True if genotype is compatible with illumina TOP coding

    Returns:
        bool: True if in top coordinates
    """

    # get illumina data as an array
    top = location.illumina_top.split("/")

    for allele in genotype:
        # mind to missing values. If missing can't be equal to illumina_top
        if allele == missing:
            continue

        if allele not in top:
            return False

    return True


def clean_chrom(chrom: str):
    """Return 0 if chrom is 99 (unmapped for snpchimp)

    Args:
        chrom (str): the (SNPchiMp) chromsome

    Returns:
        str: 0 if chrom == 99 else chrom

    """

    # forcing type (should be string by database constraints)
    if str(chrom) == "99":
        return "0"

    return chrom


@click.command()
@click.option('--mapfile', type=str, required=True)
@click.option('--pedfile', type=str, required=True)
@click.option(
    '--dataset', type=str, required=True,
    help="The raw dataset file name (zip archive)"
)
def main(mapfile, pedfile, dataset):
    """Read sample names from map/ped files and updata smarter database (insert
    a record if necessary and define a smarter id for each sample)
    """

    logger.info(f"{Path(__file__).name} started")

    # connect to database
    global_connection()

    # get the dataset object
    dataset = Dataset.objects(file=dataset).get()

    logger.debug(f"Found {dataset}")

    # determine the SampleClass
    if dataset.species == 'Sheep':
        SampleSpecies = SampleSheep
    else:
        raise NotImplementedError(
            f"Species '{dataset.species}' not yet implemented"
        )

    # check files are in dataset
    if mapfile not in dataset.contents or pedfile not in dataset.contents:
        logger.critical(
            "Couldn't find files in dataset: check for both "
            f"'{mapfile}' and '{pedfile}' in '{dataset}'")
        return

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        logger.critical("Could find dataset directory {working_dir}")
        return

    # determine full file paths
    mappath = working_dir / mapfile
    pedpath = working_dir / pedfile

    sniffer = csv.Sniffer()

    # deal with map file first
    mapdata = []

    with open(mappath) as handle:
        logger.debug(f"Reading '{mappath}' content")

        dialect = sniffer.sniff(handle.read(2048))
        handle.seek(0)
        reader = csv.reader(handle, dialect=dialect)

        mapdata = list(reader)

    for line in itertools.islice(mapdata, 5):
        logger.debug(line)

    logger.info(f"Read {len(mapdata)} snps from {mappath}")

    logger.info("Writing a new map file with updated coordinates")

    output_dir = working_dir / "OARV3"
    output_dir.mkdir(exist_ok=True)
    output_map = Path(mapfile).stem + "_updated" + Path(mapfile).suffix
    output_map = output_dir / output_map

    # I need to track genotypes
    locations = list()

    with open(output_map, 'w') as handle:
        writer = csv.writer(handle, delimiter=' ', lineterminator="\n")

        tqdm_out = TqdmToLogger(logger, level=logging.INFO)

        for line in tqdm(mapdata, file=tqdm_out, mininterval=1):
            variant = VariantSheep.objects(name=line[1]).get()
            location = variant.get_location(version='Oar_v3.1')

            # track data for this location
            locations.append(location)

            writer.writerow([
                clean_chrom(location.chrom),
                line[1],
                line[2],
                location.position
            ])

    logger.debug(f"collected {len(locations)} in 'Oar_v3.1' coordinates")

    # opening ped file for writing updated genotypes
    output_ped = Path(pedfile).stem + "_updated" + Path(pedfile).suffix
    output_ped = output_dir / output_ped

    handle_ped = open(output_ped, "w")
    writer = csv.writer(handle_ped, delimiter=' ', lineterminator="\n")

    with open(pedpath) as handle:
        logger.debug(f"Reading '{pedpath}' content")

        dialect = sniffer.sniff(handle.read(2048))
        handle.seek(0)
        reader = csv.reader(handle, dialect=dialect)

        for i, line in enumerate(reader):
            # check genotypes size 2*mapdata (diploidy) + 6 extra columns:
            if len(line) != len(mapdata)*2 + 6:
                logger.critical(
                    f"SNPs sizes don't match in '{mapfile}' and '{pedfile}'")
                logger.critical("Please check file contents")
                return

            logger.debug(f"Processing {line[:10]+ ['...']}")

            # check for breed in database
            breed = Breed.objects(
                Q(name=line[0]) | Q(aliases__in=[line[0]])
            ).get()

            logger.debug(f"Found breed {breed}")

            # search for sample in database
            qs = SampleSpecies.objects(original_id=line[1])

            if qs.count() == 1:
                logger.debug(f"Sample '{line[1]}' found in database")
                sample = qs.get()

                # TODO: update records if necessary

            else:
                # nsert sample into database
                logger.info(f"Registering sample '{line[1]}' in database")
                sample = SampleSheep(
                    original_id=line[1],
                    country=dataset.country,
                    species=dataset.species,
                    breed=breed.name,
                    breed_code=breed.code,
                    dataset=dataset
                )
                sample.save()

                # incrementing breed n_individuals counter
                breed.n_individuals += 1
                breed.save()

            # updating ped line with smarter ids
            line[0] = breed.code
            line[1] = sample.smarter_id

            # ok now is time to update genotypes
            for j in range(len(mapdata)):
                # get the proper position
                location = locations[j]

                # replacing the i-th genotypes. Skip 6 columns
                a1 = line[6+j*2]
                a2 = line[6+j*2+1]

                genotype = [a1, a2]

                if not is_top(genotype, location):
                    raise Exception("Not illumina top format")

            # write updated line into updated ped file
            logger.info(f"Writing: {line[:10]+ ['...']}")
            writer.writerow(line)

        logger.info(f"Processed {i+1} individuals")

    # closing output ped file
    handle_ped.close()

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
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    main()
