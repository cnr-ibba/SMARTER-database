#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 15:58:40 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Try to model data operations on plink files
"""

import io
import csv
import logging
from dataclasses import dataclass

from tqdm import tqdm
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q

from .snpchimp import clean_chrom
from .smarterdb import VariantSheep, SampleSheep, Breed, Dataset
from .utils import TqdmToLogger


# Get an instance of a logger
logger = logging.getLogger(__name__)


@dataclass
class MapRecord():
    chrom: str
    name: str
    cm: str
    position: int

    def __post_init__(self):
        # types are annotations. So, enforce position type:
        self.position = int(self.position)


def get_reader(handle: io.TextIOWrapper):
    logger.debug(f"Reading '{handle.name}' content")

    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(handle.read(2048))
    handle.seek(0)
    return csv.reader(handle, dialect=dialect)


class TextPlinkIO():
    mapfile = None
    pedfile = None
    mapdata = list()
    locations = list()
    filtered = set()
    _species = None
    VariantSpecies = None
    SampleSpecies = None

    def __init__(
            self,
            prefix: str = None,
            mapfile: str = None,
            pedfile: str = None,
            species: str = None):

        if prefix:
            self.mapfile = prefix + ".map"
            self.pedfile = prefix + ".ped"

        elif mapfile and pedfile:
            self.mapfile = mapfile
            self.pedfile = pedfile

        if species:
            self.species = species

    @property
    def species(self):
        return self._species

    @species.setter
    def species(self, species):
        # determine the SampleClass
        if species == 'Sheep':
            self.VariantSpecies = VariantSheep
            self.SampleSpecies = SampleSheep

        else:
            raise NotImplementedError(
                f"Species '{species}' not yet implemented"
            )

        self._species = species

    def read_mapfile(self):
        """Read map data and track informations in memory. Useful to process
        data files"""

        with open(self.mapfile) as handle:
            reader = get_reader(handle)
            self.mapdata = [MapRecord(*record) for record in reader]

    def update_mapfile(self, outputfile: str):
        # helper function to get default value for cM
        def get_cM(record):
            """Returns distance in cM or '0' (default for map file)"""

            if hasattr(record, 'cm'):
                return record.cm

            return '0'

        with open(outputfile, 'w') as handle:
            writer = csv.writer(handle, delimiter=' ', lineterminator="\n")

            for idx, record in enumerate(self.mapdata):
                if idx in self.filtered:
                    logger.warning(f"Skipping {record}: not in database")
                    continue

                # get a location relying on indexes
                location = self.locations[idx]

                # a new record in mapfile
                writer.writerow([
                    clean_chrom(location.chrom),
                    record.name,
                    get_cM(record),
                    location.position
                ])

    def get_or_create_sample(self, line: list, dataset: Dataset, breed: Breed):
        # search for sample in database
        qs = self.SampleSpecies.objects(original_id=line[1])

        if qs.count() == 1:
            logger.debug(f"Sample '{line[1]}' found in database")
            sample = qs.get()

            # TODO: update records if necessary

        else:
            # insert sample into database
            logger.info(f"Registering sample '{line[1]}' in database")
            sample = self.SampleSpecies(
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

        return sample

    def _process_genotypes(self, line: list, coding: str):
        new_line = line.copy()

        # ok now is time to update genotypes
        for j in range(len(self.mapdata)):
            # replacing the i-th genotypes. Skip 6 columns
            a1 = new_line[6+j*2]
            a2 = new_line[6+j*2+1]

            genotype = [a1, a2]

            # is this snp filtered out
            if j in self.filtered:
                logger.debug(
                    f"Skipping {self.mapdata[j].name}:[{a1}/{a2}] "
                    "not in database!"
                )

                continue

            # get the proper position
            location = self.locations[j]

            # TODO: coding need to be a dataset attribute
            if coding == 'top':
                if not location.is_top(genotype):
                    logger.critical(
                        f"Error for {self.mapdata[j].name}: "
                        f"{a1}/{a2} <> {location.illumina_top}"
                    )
                    raise Exception("Not illumina top format")

            elif coding == 'forward':
                if not location.is_forward(genotype):
                    logger.critical(
                        f"Error for {self.mapdata[j].name}: "
                        f"{a1}/{a2} <> {location.illumina_top}"
                    )
                    raise Exception("Not illumina forward format")

                # change the allele coding
                top_genotype = location.forward2top(genotype)
                new_line[6+j*2], new_line[6+j*2+1] = top_genotype

            else:
                raise NotImplementedError(f"Coding '{coding}' not supported")

        return new_line

    def _process_pedline(self, line: list, dataset: Dataset, coding: str):
        # check genotypes size 2*mapdata (diploidy) + 6 extra columns:
        if len(line) != len(self.mapdata)*2 + 6:
            logger.critical(
                f"SNPs sizes don't match in '{self.mapfile}' "
                "and '{self.pedfile}'")
            logger.critical("Please check file contents")
            return

        logger.debug(f"Processing {line[:10]+ ['...']}")

        # check for breed in database
        breed = Breed.objects(
            Q(name=line[0]) | Q(aliases__in=[line[0]])
        ).get()

        logger.debug(f"Found breed {breed}")

        # check for sample in database
        sample = self.get_or_create_sample(line, dataset, breed)

        # a new line obj
        new_line = line.copy()

        # updating ped line with smarter ids
        new_line[0] = breed.code
        new_line[1] = sample.smarter_id

        # check and fix genotypes if necessary
        new_line = self._process_genotypes(new_line, coding)

        # need to remove filtered snps from ped line
        for index in sorted(self.filtered, reverse=True):
            # index is snp position. Need to delete two fields
            del new_line[6+index*2+1]
            del new_line[6+index*2]

        return new_line

    def read_pedfile(self):
        """Open pedfile for reading return iterator"""

        with open(self.pedfile) as handle:
            reader = get_reader(handle)
            for line in reader:
                yield line

    def update_pedfile(self, outputfile: str, dataset: Dataset, coding: str):
        """Update ped contents"""

        with open(outputfile, "w") as target:
            writer = csv.writer(
                target, delimiter=' ', lineterminator="\n")

            for i, line in enumerate(self.read_pedfile()):
                new_line = self._process_pedline(line, dataset, coding)

                # write updated line into updated ped file
                logger.info(
                    f"Writing: {new_line[:10]+ ['...']} "
                    f"({int((len(new_line)-6)/2)} SNPs)")
                writer.writerow(new_line)

            logger.info(f"Processed {i+1} individuals")

            # output file block

        # input file block

    def fetch_coordinates(self, version: str):
        """Search for variants in smarter database"""

        # reset meta informations
        self.locations = list()
        self.filtered = set()

        tqdm_out = TqdmToLogger(logger, level=logging.INFO)

        for idx, record in enumerate(tqdm(
                self.mapdata, file=tqdm_out, mininterval=1)):
            try:
                variant = self.VariantSpecies.objects(name=record.name).get()

            except DoesNotExist as e:
                logger.error(f"Couldn't find {record.name}: {e}")

                # skip this variant (even in ped)
                self.filtered.add(idx)

                # need to add an empty value in locations (or my indexes
                # won't work properly)
                self.locations.append(None)

                continue

            # get location for snpchimp (defalt) in oarv3.1 coordinates
            location = variant.get_location(version=version)

            # track data for this location
            self.locations.append(location)

        logger.debug(
            f"collected {len(self.locations)} in '{version}' coordinates")
