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
from plinkio import plinkfile

from .snpchimp import clean_chrom
from .smarterdb import (
    VariantSheep, SampleSheep, Breed, Dataset, SmarterDBException, SEX)
from .utils import TqdmToLogger
from .illumina import read_snpList, read_illuminaRow


# Get an instance of a logger
logger = logging.getLogger(__name__)


class CodingException(Exception):
    pass


class IlluminaReportException(Exception):
    pass


@dataclass
class MapRecord():
    chrom: str
    name: str
    cm: float
    position: int

    def __post_init__(self):
        # types are annotations. So, enforce position type:
        self.position = int(self.position)
        self.cm = float(self.cm)


def get_reader(handle: io.TextIOWrapper):
    logger.debug(f"Reading '{handle.name}' content")

    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(handle.read(2048))
    handle.seek(0)
    return csv.reader(handle, dialect=dialect)


class SmarterMixin():
    """Common features of a Smarter related dataset file"""

    _species = None
    mapdata = list()
    locations = list()
    filtered = set()
    VariantSpecies = None
    SampleSpecies = None
    chip_name = None

    # this need to be set to the proper read genotype method
    read_genotype_method = None

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

    def get_breed(self, fid, *args, **kwargs):
        if len(args) > 0:
            dataset = args[0]

        if 'dataset' in kwargs:
            dataset = kwargs['dataset']

        # this is a $elemMatch query
        breed = Breed.objects(
            aliases__match={'fid': fid, 'dataset': dataset}).get()

        logger.debug(f"Found breed {breed}")

        return breed

    def get_country(self, dataset: Dataset, breed: Breed):
        # this will be the default value
        country = dataset.country

        # search for country in my aliases
        for alias in breed.aliases:
            if alias.dataset != dataset:
                continue

            if alias.country:
                # override country if defined
                country = alias.country

        return country

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

    def _deal_with_relationship(self, line: list, dataset: Dataset):
        # deal with special items
        sex = None
        father_id = None
        mother_id = None

        # test with sex column
        if int(line[4]) in [1, 2]:
            sex = SEX(int(line[4]))

        # test with father id
        if str(line[2]) != '0':
            qs = self.SampleSpecies.objects(
                original_id=line[2], dataset=dataset)

            if qs.count() == 1:
                father_id = qs.get()

        # test with mother id
        if str(line[3]) != '0':
            qs = self.SampleSpecies.objects(
                original_id=line[3], dataset=dataset)

            if qs.count() == 1:
                mother_id = qs.get()

        return sex, father_id, mother_id

    def get_or_create_sample(self, line: list, dataset: Dataset, breed: Breed):
        # search for sample in database
        qs = self.SampleSpecies.objects(
            original_id=line[1], dataset=dataset)

        sex, father_id, mother_id = self._deal_with_relationship(
            line, dataset)

        if qs.count() == 1:
            logger.debug(f"Sample '{line[1]}' found in database")
            sample = qs.get()

            # TODO: update records if necessary

        elif qs.count() == 0:
            # do I have a multi country dataset?
            country = self.get_country(dataset, breed)

            # insert sample into database
            logger.info(f"Registering sample '{line[1]}' in database")
            sample = self.SampleSpecies(
                original_id=line[1],
                country=country,
                species=dataset.species,
                breed=breed.name,
                breed_code=breed.code,
                dataset=dataset,
                chip_name=self.chip_name,
                sex=sex,
                father_id=father_id,
                mother_id=mother_id
            )
            sample.save()

            # incrementing breed n_individuals counter
            breed.n_individuals += 1
            breed.save()

        else:
            raise SmarterDBException(
                f"Got {qs.count()} results for '{line[1]}'")

        return sample

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
                    raise CodingException("Not illumina top format")

            elif coding == 'forward':
                if not location.is_forward(genotype):
                    logger.critical(
                        f"Error for {self.mapdata[j].name}: "
                        f"{a1}/{a2} <> {location.illumina_top}"
                    )
                    raise CodingException("Not illumina forward format")

                # change the allele coding
                top_genotype = location.forward2top(genotype)
                new_line[6+j*2], new_line[6+j*2+1] = top_genotype

            elif coding == 'ab':
                if not location.is_ab(genotype):
                    logger.critical(
                        f"Error for {self.mapdata[j].name}: "
                        f"{a1}/{a2} <> {location.illumina_top}"
                    )
                    raise CodingException("Not illumina ab format")

                # change the allele coding
                top_genotype = location.ab2top(genotype)
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

        # check for breed in database reling on fid.
        try:
            breed = self.get_breed(fid=line[0], dataset=dataset)

        except DoesNotExist as e:
            logger.error(e)
            raise SmarterDBException(
                f"Couldn't find fid '{line[0]}': {line[:10]+ ['...']}"
            )

        # check for sample in database
        sample = self.get_or_create_sample(line, dataset, breed)

        # a new line obj
        new_line = line.copy()

        # updating ped line with smarter ids
        new_line[0] = breed.code
        new_line[1] = sample.smarter_id

        # add father or mather to ped line
        if sample.father_id:
            new_line[2] = sample.father_id.smarter_id

        if sample.mother_id:
            new_line[3] = sample.mother_id.smarter_id

        # check and fix genotypes if necessary
        new_line = self._process_genotypes(new_line, coding)

        # need to remove filtered snps from ped line
        for index in sorted(self.filtered, reverse=True):
            # index is snp position. Need to delete two fields
            del new_line[6+index*2+1]
            del new_line[6+index*2]

        return new_line

    def update_pedfile(
            self, outputfile: str, dataset: Dataset, coding: str,
            *args, **kwargs):
        """Update ped contents"""

        with open(outputfile, "w") as target:
            writer = csv.writer(
                target, delimiter=' ', lineterminator="\n")

            for i, line in enumerate(
                    self.read_genotype_method(*args, **kwargs)):
                new_line = self._process_pedline(line, dataset, coding)

                # write updated line into updated ped file
                logger.info(
                    f"Writing: {new_line[:10]+ ['...']} "
                    f"({int((len(new_line)-6)/2)} SNPs)")
                writer.writerow(new_line)

            logger.info(f"Processed {i+1} individuals")

            # output file block

        # input file block


class TextPlinkIO(SmarterMixin):
    mapfile = None
    pedfile = None

    def __init__(
            self,
            prefix: str = None,
            mapfile: str = None,
            pedfile: str = None,
            species: str = None,
            chip_name: str = None):

        # need to be set in order to write a genotype
        self.read_genotype_method = self.read_pedfile

        if prefix:
            self.mapfile = prefix + ".map"
            self.pedfile = prefix + ".ped"

        elif mapfile or pedfile:
            self.mapfile = mapfile
            self.pedfile = pedfile

        if species:
            self.species = species

        if chip_name:
            self.chip_name = chip_name

    def read_mapfile(self):
        """Read map data and track informations in memory. Useful to process
        data files"""

        with open(self.mapfile) as handle:
            reader = get_reader(handle)
            self.mapdata = [MapRecord(*record) for record in reader]

    def read_pedfile(self):
        """Open pedfile for reading return iterator"""

        with open(self.pedfile) as handle:
            reader = get_reader(handle)
            for line in reader:
                yield line


class BinaryPlinkIO(SmarterMixin):
    plink_file = None
    _prefix = None

    def __init__(
            self,
            prefix: str = None,
            species: str = None,
            chip_name: str = None):

        # need to be set in order to write a genotype
        self.read_genotype_method = self.read_pedfile

        if prefix:
            self.prefix = prefix

        if species:
            self.species = species

        if chip_name:
            self.chip_name = chip_name

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: str):
        self._prefix = prefix
        self.plink_file = plinkfile.open(self._prefix)

    def read_mapfile(self):
        """Read map data and track informations in memory. Useful to process
        data files"""

        self.mapdata = list()

        for locus in self.plink_file.get_loci():
            record = MapRecord(
                chrom=locus.chromosome,
                name=locus.name,
                position=locus.bp_position,
                cm=locus.position
            )
            self.mapdata.append(record)

    def read_pedfile(self):
        """Open pedfile for reading return iterator"""

        sample_list = self.plink_file.get_samples()
        locus_list = self.plink_file.get_loci()
        snp_arrays = list(self.plink_file)

        def format_sex(value):
            if value in [1, 2]:
                return str(value)
            else:
                return "0"

        def convert(genotype, locus):
            # in binary format, allele2 is REF allele1 ALT
            if genotype == 0:
                return locus.allele1, locus.allele1
            elif genotype == 1:
                return locus.allele2, locus.allele1
            elif genotype == 2:
                return locus.allele2, locus.allele2
            elif genotype == 3:
                return "0", "0"
            else:
                raise CodingException("Genotype %s Not supported" % genotype)

        # determine genotype length
        size = 6 + 2*len(self.mapdata)

        for sample_idx, sample in enumerate(sample_list):
            # this will be the returned row
            line = ["0"] * size

            # set values. I need to set a breed code in order to get a
            # proper ped line
            line[0:6] = [
                sample.fid,
                sample.iid,
                sample.father_iid,
                sample.mother_iid,
                format_sex(sample.sex),
                int(sample.phenotype)
            ]

            for idx, locus in enumerate(locus_list):
                genotype = snp_arrays[idx][sample_idx]
                line[6+idx*2], line[6+idx*2+1] = convert(genotype, locus)

            yield line


class IlluminaReportIO(SmarterMixin):
    snpfile = None
    report = None

    def __init__(
            self,
            snpfile: str = None,
            report: str = None,
            species: str = None,
            chip_name: str = None):

        # need to be set in order to write a genotype
        self.read_genotype_method = self.read_reportfile

        if snpfile or report:
            self.snpfile = snpfile
            self.report = report

        if species:
            self.species = species

        if chip_name:
            self.chip_name = chip_name

    def get_breed(self, fid, *args, **kwargs):
        # this is a $elemMatch query
        breed = Breed.objects(code=fid).get()

        logger.debug(f"Found breed {breed}")

        return breed

    def read_snpfile(self):
        """Read snp data and track informations in memory. Useful to process
        data files"""

        self.mapdata = list(read_snpList(self.snpfile))

    def read_reportfile(self, fid: str):
        """Open illumina report returns iterator"""

        # determine genotype length
        size = 6 + 2*len(self.mapdata)

        # track sample
        last_sample = None

        # need to have snp indexes
        indexes = [record.name for record in self.mapdata]

        # this will be the returned row
        line = list()

        # this is the snp position index
        idx = 0

        # tray to returns something like a ped row
        for row in read_illuminaRow(self.report):
            if row.sample_id != last_sample:
                logger.debug(f"Reading sample {row.sample_id}")
                if last_sample:
                    yield line

                # initialize an empty array
                line = ["0"] * size

                # set values. I need to set a breed code in order to get a
                # proper ped line
                line[0], line[1], line[5] = fid, row.sample_id, -9

                # track last sample
                last_sample = row.sample_id

                # reset index
                idx = 0

            # check snp name consistency
            if indexes[idx] != row.snp_name:
                raise IlluminaReportException(
                    f"snp positions doens't match "
                    f"{indexes[idx]}<>{row.snp_name}"
                )

            # update line relying on records
            line[6+idx*2], line[6+idx*2+1] = row.allele1_ab, row.allele2_ab

            # updating indexes
            idx += 1

        # after completing rows, I need to return last one
        yield line
