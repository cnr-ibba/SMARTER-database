#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 15:58:40 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Try to model data operations on plink files
"""

import csv
import logging
from dataclasses import dataclass

from tqdm import tqdm
from mongoengine.errors import DoesNotExist

from .snpchimp import clean_chrom
from .smarterdb import VariantSheep
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


class TextPlinkIO():
    mapfile = None
    pedfile = None
    mapdata = list()
    locations = list()
    filtered = set()

    def __init__(
            self,
            prefix: str = None,
            mapfile: str = None,
            pedfile: str = None):
        if prefix:
            self.mapfile = prefix + ".map"
            self.pedfile = prefix + ".ped"

        elif mapfile and pedfile:
            self.mapfile = mapfile
            self.pedfile = pedfile

        if self.mapfile:
            self.read_mapfile()

    def read_mapfile(self):
        """Read map data and track informations in memory. Useful to process
        data files"""

        sniffer = csv.Sniffer()

        with open(self.mapfile) as handle:
            logger.debug(f"Reading '{self.mapfile}' content")

            dialect = sniffer.sniff(handle.read(2048))
            handle.seek(0)
            reader = csv.reader(handle, dialect=dialect)

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

    def fetch_coordinates(self, species: str, version: str):
        """Search for variants in smarter database"""

        # reset meta informations
        self.locations = list()
        self.filtered = set()

        # determine the SampleClass
        if species == 'Sheep':
            VariantSpecies = VariantSheep
        else:
            raise NotImplementedError(
                f"Species '{species}' not yet implemented"
            )

        tqdm_out = TqdmToLogger(logger, level=logging.INFO)

        for idx, record in enumerate(tqdm(
                self.mapdata, file=tqdm_out, mininterval=1)):
            try:
                variant = VariantSpecies.objects(name=record.name).get()

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
