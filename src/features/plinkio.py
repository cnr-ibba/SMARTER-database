#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 15:58:40 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Try to model data operations on plink files
"""

import re
import csv
import logging

from pathlib import Path
from typing import Union
from collections import namedtuple
from dataclasses import dataclass

from tqdm import tqdm
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned
from mongoengine.queryset import Q
from plinkio import plinkfile

from .snpchimp import clean_chrom
from .smarterdb import (
    VariantSheep, SampleSheep, Breed, Dataset, SmarterDBException, SEX,
    VariantGoat, SampleGoat, Location, get_sample_type)
from .utils import TqdmToLogger, skip_comments, text_or_gzip_open
from .illumina import read_snpList, read_illuminaRow
from .affymetrix import read_affymetrixRow

# Get an instance of a logger
logger = logging.getLogger(__name__)

# a generic class to deal with assemblies
AssemblyConf = namedtuple('AssemblyConf', ['version', 'imported_from'])


class CodingException(Exception):
    pass


class PlinkIOException(Exception):
    pass


class IlluminaReportException(Exception):
    pass


class AffyReportException(Exception):
    pass


@dataclass
class MapRecord():
    chrom: str
    name: str
    cm: float
    position: int

    def __post_init__(self):
        # types are annotations. So, enforce position type:
        if isinstance(self.position, str):
            if self.position.isnumeric():
                self.position = int(self.position)

        if isinstance(self.cm, str):
            if self.cm.isnumeric():
                self.cm = float(self.cm)


class SmarterMixin():
    """Common features of a Smarter related dataset file"""

    _species = None
    mapdata = list()
    src_locations = list()
    dst_locations = list()
    filtered = set()
    variants_name = list()
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
        if not species:
            # avoid to check a None value
            return

        # determine the SampleClass
        elif species == 'Sheep':
            self.VariantSpecies = VariantSheep
            self.SampleSpecies = SampleSheep

        elif species == 'Goat':
            self.VariantSpecies = VariantGoat
            self.SampleSpecies = SampleGoat

        else:
            raise NotImplementedError(
                f"Species '{species}' not yet implemented"
            )

        self._species = species

    def search_breed(self, fid, dataset, *args, **kwargs):
        """Get breed relying aliases and dataset"""

        # this is a $elemMatch query
        breed = Breed.objects(
            aliases__match={'fid': fid, 'dataset': dataset}).get()

        logger.debug(f"Found breed {breed}")

        return breed

    def search_country(self, dataset: Dataset, breed: Breed):
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
            counter = 0

            for idx, record in enumerate(self.mapdata):
                if idx in self.filtered:
                    logger.warning(f"Skipping {record}: not in database")
                    continue

                # get a location relying on indexes
                location = self.dst_locations[idx]

                # get the tracked variant name relying on indexes
                variant_name = self.variants_name[idx]

                # a new record in mapfile
                writer.writerow([
                    clean_chrom(location.chrom),
                    variant_name,
                    get_cM(record),
                    location.position
                ])

                counter += 1

        logger.info(f"Wrote {counter} SNPs in mapfile")

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

    def _create_sample(
            self,
            line: list,
            dataset: Dataset,
            breed: Breed,
            sex: SEX,
            father_id: Union[SampleSheep, SampleGoat],
            mother_id: Union[SampleSheep, SampleGoat]) -> Union[
                SampleSheep, SampleGoat]:
        """
        Helper method to create a new sample from a PED line

        Parameters
        ----------
        line : list
            A PED line.
        dataset : Dataset
            The Dataset instance this sample belong to.
        breed : Breed
            The Breed instance of this sample.
        sex : SEX
            The sex of this sample (if any).
        father_id : Union[SampleSheep, SampleGoat]
            The father of this sample (if any).
        mother_id : Union[SampleSheep, SampleGoat]
            The mother of this sample (if any).

        Returns
        -------
        Union[SampleSheep, SampleGoat]
            The created sample instance.
        """

        # do I have a multi country dataset? try to determine the country
        country = self.search_country(dataset, breed)

        # test if foreground or background dataset
        type_ = get_sample_type(dataset)

        # insert sample into database
        logger.info(f"Registering sample '{line[1]}' in database")

        sample = self.SampleSpecies(
            original_id=line[1],
            country=country,
            breed=breed.name,
            breed_code=breed.code,
            dataset=dataset,
            type_=type_,
            chip_name=self.chip_name,
            sex=sex,
            father_id=father_id,
            mother_id=mother_id
        )
        sample.save()

        logger.debug(f"Increment '{breed}' n_individuals counter")

        breed.n_individuals += 1
        breed.save()

        return sample

    def get_or_create_sample(
            self,
            line: list,
            dataset: Dataset,
            breed: Breed,
            sample_field: str = "original_id",
            create_sample: bool = False) -> Union[SampleSheep, SampleGoat]:
        """
        Get a sample from database or create a new one (if create_sample
        parameter flag is provided)

        Parameters
        ----------
        line : list
            A ped line as a list.
        dataset : Dataset
            The dataset object this sample belongs to.
        breed : Breed
            The Breed object of such sample.
        sample_field : str, optional
            Search sample name within this field. The default is "original_id".
        create_sample : bool, optional
            Create a sample if not found in database. The default is False.

        Raises
        ------
        SmarterDBException
            Raised if more than one sample is retrieved.

        Returns
        -------
        sample : Union[SampleSheep, SampleGoat]
            A SampleSheep or SampleGoat object for a Sample object found or
            created. None if no sample is found and create_sample if False.
        """

        # search for sample in database
        qs = self.SampleSpecies.objects(
            dataset=dataset,
            breed_code=breed.code,
            **{sample_field: line[1]}
        )

        sex, father_id, mother_id = self._deal_with_relationship(
            line, dataset)

        # the sample I want to return
        sample = None

        if qs.count() == 1:
            logger.debug(f"Sample '{line[1]}' found in database")
            sample = qs.get()

            # update records if necessary
            if sample.father_id != father_id or sample.mother_id != mother_id:
                logger.warning(f"Update relationships for sample '{line[1]}'")
                sample.father_id = father_id
                sample.mother_id = mother_id
                sample.save()

        elif qs.count() == 0:
            if not create_sample:
                logger.warning(f"Sample '{line[1]}' not found in database")

            else:
                sample = self._create_sample(
                    line, dataset, breed, sex, father_id, mother_id)

        else:
            raise SmarterDBException(
                f"Got {qs.count()} results for '{line[1]}'")

        return sample

    # helper function
    def skip_index(self, idx):
        """Skip a certain SNP reling on its position"""

        # skip this variant (even in ped)
        self.filtered.add(idx)

        # need to add an empty value in locations (or my indexes
        # won't work properly). The same for variants name
        self.src_locations.append(None)
        self.dst_locations.append(None)
        self.variants_name.append(None)

    def make_query_args(
            self, src_assembly: AssemblyConf, dst_assembly: AssemblyConf):
        """Generate args to select variants from database"""

        query = []

        # construct the query arguments to search into database
        if dst_assembly:
            query = [Q(locations__match=src_assembly._asdict()) &
                     Q(locations__match=dst_assembly._asdict())]
        else:
            query = [Q(locations__match=src_assembly._asdict())]

        return query

    def make_query_kwargs(
            self, search_field: str, record: MapRecord, chip_name: str):
        """Generate kwargs to select variants from database"""

        if search_field == 'probeset_id':
            # construct a custom query to find the selected SNP
            return {
                "probesets__match": {
                    'chip_name': chip_name,
                    'probeset_id': record.name
                }
            }

        else:
            return {
                search_field: record.name,
                "chip_name": chip_name
            }

    def fetch_coordinates(
            self,
            src_assembly: AssemblyConf,
            dst_assembly: AssemblyConf = None,
            search_field: str = "name",
            chip_name: str = None,
            *args, **kwargs):
        """Search for variants in smarter database

        Args:
            src_assembly (AssemblyConf): the source data assembly version
            dst_assembly (AssemblyConf): the destination data assembly version
            search_field (str): search variant by field (def. "name")
            chip_name (str): limit search to this chip_name
        """

        # reset meta informations
        self.src_locations = list()
        self.dst_locations = list()
        self.filtered = set()
        self.variants_name = list()

        # get the query arguments relying on assemblies
        query = self.make_query_args(src_assembly, dst_assembly)

        tqdm_out = TqdmToLogger(logger, level=logging.INFO)

        for idx, record in enumerate(tqdm(
                self.mapdata, file=tqdm_out, mininterval=1)):
            try:
                # additional arguments used in query
                additional_arguments = self.make_query_kwargs(
                    search_field, record, chip_name)

                # remove empty additional arguments if any
                variant = self.VariantSpecies.objects(
                    *query,
                    **{k: v for k, v in additional_arguments.items() if v}
                ).get()

            except DoesNotExist as e:
                logger.debug(
                    f"Couldn't find '{record.name}' with '{query}'"
                    f"using '{additional_arguments}': {e}")

                self.skip_index(idx)

                # don't check location for missing SNP
                continue

            except MultipleObjectsReturned as e:
                logger.warning(
                    f"Got multiple {record.name} with '{query}'"
                    f"using '{additional_arguments}': {e}")

                self.skip_index(idx)

                # don't check location for missing SNP
                continue

            # get the proper locations and track it
            src_location = variant.get_location(**src_assembly._asdict())
            self.src_locations.append(src_location)

            if dst_assembly:
                dst_location = variant.get_location(**dst_assembly._asdict())
                self.dst_locations.append(dst_location)

            # track variant.name read from database (useful when searching
            # using probeset_id)
            self.variants_name.append(variant.name)

        # for simplicity
        if not dst_assembly:
            self.dst_locations = self.src_locations

        logger.debug(
            f"collected {len(self.dst_locations)} with '{query}' "
            f"using '{additional_arguments}'")

    def fetch_coordinates_by_positions(
            self,
            src_assembly: AssemblyConf,
            dst_assembly: AssemblyConf = None):
        """
        Search for variant in smarter database relying on positions

        Parameters
        ----------
        src_assembly : AssemblyConf
            the source data assembly version.
        dst_assembly : AssemblyConf, optional
            the destination data assembly version. The default is None.

        Returns
        -------
        None.
        """

        # reset meta informations
        self.src_locations = list()
        self.dst_locations = list()
        self.filtered = set()
        self.variants_name = list()

        tqdm_out = TqdmToLogger(logger, level=logging.INFO)

        for idx, record in enumerate(tqdm(
                self.mapdata, file=tqdm_out, mininterval=1)):

            location = src_assembly._asdict()
            location["chrom"] = record.chrom
            location["position"] = record.position

            # construct the final query
            # construct the query arguments to search into database
            if dst_assembly:
                query = [Q(locations__match=location) &
                         Q(locations__match=dst_assembly._asdict())]
            else:
                query = [Q(locations__match=location)]

            try:
                variant = self.VariantSpecies.objects(
                    *query
                ).get()

            except DoesNotExist as e:
                logger.debug(
                    f"Couldn't find '{record.chrom}:{record.position}' in "
                    f"'{src_assembly}' assembly: {e}")

                self.skip_index(idx)

                # don't check location for missing SNP
                continue

            except MultipleObjectsReturned as e:
                # tecnically, I could return the first item I found in
                # my database. Skip, for the moment
                logger.debug(
                    f"Got multiple records for position '{record.chrom}:"
                    f"{record.position}' in '{src_assembly}'"
                    f" assembly: {e}")

                self.skip_index(idx)

                # don't check location for missing SNP
                continue

            # get the proper locations and track it
            src_location = variant.get_location(**src_assembly._asdict())
            self.src_locations.append(src_location)

            if dst_assembly:
                dst_location = variant.get_location(**dst_assembly._asdict())
                self.dst_locations.append(dst_location)

            # track variant.name read from database (useful when searching
            # using probeset_id)
            self.variants_name.append(variant.name)

        # for simplicity
        if not dst_assembly:
            self.dst_locations = self.src_locations

        logger.debug(
            f"collected {len(self.dst_locations)} using positions "
            f"in '{src_assembly}' assembly")

    def _to_top(
            self, index: int, genotype: list, coding: str,
            location: Location) -> list:
        """
        Check genotype with coding and returns illumina_top alleles

        Parameters
        ----------
        index: int
            The i-th SNP received
        genotype : list
            The genotype as a list (ex: ['T', 'C'])
        coding : str
            The coding input type ('top', 'forward', ...)
        location : Location
            A smarterdb location used to check input genotype and coding and
            to return the corresponing illumina top genotype (ex ['A', 'G'])

        Raises
        ------
        CodingException
            Raised when input genotype hasn't a match in the smarter database
            with the provided coding
        NotImplementedError
            A coding format not yet supported (implemented)

        Returns
        -------
        list
            The illumina top genotype as a list (ex ['A', 'G'])
        """

        # for semplicity
        a1, a2 = genotype

        # the returned value
        top_genotype = []

        # TODO: coding need to be a dataset attribute
        if coding == 'top':
            if not location.is_top(genotype):
                logger.debug(
                    f"Error for SNP {index}: '{self.mapdata[index].name}': "
                    f"{a1}/{a2} <> {location.illumina_top}"
                )
                raise CodingException(
                    f"SNP '{self.mapdata[index].name}' is "
                    "not in illumina top format")

            # allele coding is the same received as input
            top_genotype = genotype

        elif coding == 'forward':
            if not location.is_forward(genotype):
                logger.debug(
                    f"Error for SNP {index}: '{self.mapdata[index].name}': "
                    f"{a1}/{a2} <> {location.illumina_forward}"
                )
                raise CodingException(
                    f"SNP '{self.mapdata[index].name}' is "
                    "not in illumina forward format")

            # change the allele coding
            top_genotype = location.forward2top(genotype)

        elif coding == 'ab':
            if not location.is_ab(genotype):
                logger.debug(
                    f"Error for SNP {index}: '{self.mapdata[index].name}': "
                    f"{a1}/{a2} <> A/B"
                )
                raise CodingException(
                    f"SNP '{self.mapdata[index].name}' is "
                    "not in illumina ab format")

            # change the allele coding
            top_genotype = location.ab2top(genotype)

        elif coding == 'affymetrix':
            if not location.is_affymetrix(genotype):
                logger.debug(
                    f"Error for SNP {index}: '{self.mapdata[index].name}': "
                    f"{a1}/{a2} <> {location.affymetrix_ab}"
                )
                raise CodingException(
                    f"SNP '{self.mapdata[index].name}' is "
                    "not in affymetrix format")

            # change the allele coding
            top_genotype = location.affy2top(genotype)

        else:
            raise NotImplementedError(f"Coding '{coding}' not supported")

        return top_genotype

    def _process_genotypes(self, line: list, coding: str, ignore_errors=False):
        new_line = line.copy()

        # ok now is time to update genotypes
        for i in range(len(self.mapdata)):
            # replacing the i-th genotypes. Skip 6 columns
            a1 = new_line[6+i*2]
            a2 = new_line[6+i*2+1]

            genotype = [a1, a2]

            # xor condition: https://stackoverflow.com/a/433161/4385116
            if (a1 in ["0", "-"]) != (a2 in ["0", "-"]):
                logger.warning(
                    f"Found half-missing SNP in {new_line[1]}: {i*2}: "
                    f"[{a1}/{a2}]. Forcing SNP to be MISSING")

                new_line[6+i*2], new_line[6+i*2+1] = ["0", "0"]

                continue

            # is this snp filtered out
            if i in self.filtered:
                logger.debug(
                    f"Skipping {self.mapdata[i].name}:[{a1}/{a2}] "
                    "not in database!"
                )

                continue

            # get the proper position
            location = self.src_locations[i]

            # check and return illumina top genotype
            try:
                top_genotype = self._to_top(i, genotype, coding, location)

                # replace alleles in ped line with top genotype
                new_line[6+i*2], new_line[6+i*2+1] = top_genotype

            except CodingException as e:
                if ignore_errors:
                    # ok, replace with a missing genotype
                    logger.debug(
                        f"Ignoring code check in {new_line[1]}: {i*2}: "
                        f"[{a1}/{a2}]. Forcing SNP to be MISSING")

                    new_line[6+i*2], new_line[6+i*2+1] = ["0", "0"]
                    continue

                else:
                    # this is the normal case
                    raise e

        return new_line

    def _check_file_sizes(self, line):
        # check genotypes size 2*mapdata (diploidy) + 6 extra columns:
        if len(line) != len(self.mapdata)*2 + 6:
            logger.critical(
                f"SNPs sizes don't match in '{self.mapfile}' "
                f"and '{self.pedfile}'")
            logger.critical("Please check file contents")

            raise PlinkIOException(".ped line size doens't match .map size")

    def _process_relationship(self, line, sample):
        # create a copy of the original object
        new_line = line.copy()

        # add father or mather to ped line (if I can)
        if str(line[2]) != '0':
            if sample.father_id:
                new_line[2] = sample.father_id.smarter_id

            else:
                logger.warning(
                    f"Cannot resolve relationship for father {line[2]}")
                new_line[2] = '0'

        if str(line[3]) != '0':
            if sample.mother_id:
                new_line[3] = sample.mother_id.smarter_id

            else:
                logger.warning(
                    f"Cannot resolve relationship for mother {line[3]}")
                new_line[3] = '0'

        return new_line

    def _process_pedline(
            self,
            line: list,
            dataset: Dataset,
            coding: str,
            create_sample: bool = False,
            sample_field: str = "original_id",
            ignore_coding_errors: bool = False):

        self._check_file_sizes(line)

        logger.debug(f"Processing {line[:10]+ ['...']}")

        # check for breed in database reling on fid.
        try:
            breed = self.search_breed(fid=line[0], dataset=dataset)

        except DoesNotExist as e:
            logger.error(e)
            raise SmarterDBException(
                f"Couldn't find breed_code '{line[0]}': {line[:10]+ ['...']}"
            )

        # check for sample in database
        sample = self.get_or_create_sample(
            line, dataset, breed, sample_field, create_sample)

        # if I couldn't find a registered sample (in such case)
        # i can skip such record
        if not sample:
            return None

        # a new line obj
        new_line = line.copy()

        # updating ped line with smarter ids
        new_line[0] = breed.code
        new_line[1] = sample.smarter_id

        # replace relationship if possible
        new_line = self._process_relationship(new_line, sample)

        # check and fix genotypes if necessary
        new_line = self._process_genotypes(
            new_line, coding, ignore_coding_errors)

        # update ped line with sex accordingly to db informations
        if sample.sex and int(new_line[4]) != sample.sex.value:
            logger.warning(
                f"Update sex for sample '{sample} {new_line[4]} -> "
                f"{sample.sex.value}'")
            new_line[4] = str(sample.sex.value)

        # need to remove filtered snps from ped line
        for index in sorted(self.filtered, reverse=True):
            # index is snp position. Need to delete two fields
            del new_line[6+index*2+1]
            del new_line[6+index*2]

        return new_line

    def update_pedfile(
            self,
            outputfile: str,
            dataset: Dataset,
            coding: str,
            create_samples: bool = False,
            sample_field: str = "original_id",
            ignore_coding_errors: bool = False,
            *args,
            **kwargs):
        """
        Write a new pedfile relying on illumina_top genotypes and coordinates
        stored in smarter database

        Args:
            outputfile (str): write ped to this path (overwrite if exists)
            dataset (Dataset): the dataset we are converting
            coding (str): the source coding (could be 'top', 'ab', 'forward')
            create_samples (bool): create samples if not exist (useful to
                create samples directly from ped file)
            sample_field (str): search samples using this attribute (def.
                'original_id')
            ignore_coding_errors (bool): ignore coding related errors (no
                more exceptions when genotypes don't match)
        """

        if ignore_coding_errors:
            logger.warning(
                "Coding check is disabled! wrong genotypes will not "
                "throw errors!")

        with open(outputfile, "w") as target:
            writer = csv.writer(
                target, delimiter=' ', lineterminator="\n")

            processed = 0

            for line in self.read_genotype_method(
                    dataset=dataset,
                    sample_field=sample_field,
                    *args, **kwargs):

                # covert the ped line with the desidered format
                new_line = self._process_pedline(
                    line,
                    dataset,
                    coding,
                    create_samples,
                    sample_field,
                    ignore_coding_errors)

                if new_line:
                    # write updated line into updated ped file
                    logger.debug(
                        f"Writing: {new_line[:10]+ ['...']} "
                        f"({int((len(new_line)-6)/2)} SNPs)")
                    writer.writerow(new_line)

                    processed += 1

                else:
                    logger.warning(
                        f"Skipping: {line[:10]+ ['...']} "
                        f"({int((len(line)-6)/2)} SNPs)"
                    )

            logger.info(f"Processed {processed} individuals")

            # output file block

        # input file block


class FakePedMixin():
    """Class which override SmarterMixin when creating a PED file from a
    non-plink file format. In this case the FID is already correct and I don't
    need to look for dataset aliases"""

    def search_breed(self, fid, *args, **kwargs):
        """Get breed relying on provided FID and species class attribute"""

        breed = Breed.objects(code=fid, species=self.species).get()

        logger.debug(f"Found breed {breed}")

        return breed

    def search_fid(
            self,
            sample_name: str,
            dataset: Dataset,
            sample_field: str = "original_id"
            ) -> str:
        """
        Determine FID from smarter SampleSpecies breed

        Parameters
        ----------
        sample_name : str
            The sample name.
        dataset : Dataset
            The dataset where the sample comes from.
        sample_field : str
            The field use to search sample name

        Returns
        -------
        fid : str
            The FID used in the generated .ped file
        """

        logger.debug(
            f"Searching fid for sample using {sample_field}: '{sample_name}, "
            "{dataset}'")

        # determine fid from sample, if not received as argument
        try:
            sample = self.SampleSpecies.objects.get(
                dataset=dataset,
                **{sample_field: sample_name}
            )
        except DoesNotExist as e:
            logger.debug(e)
            raise SmarterDBException(
                f"Couldn't find sample '{sample_name}' in file "
                f"'{dataset.file}' using field'{sample_field}'"
            )

        fid = sample.breed_code
        logger.debug(
            f"Found breed '{fid}' for '{sample_name}'")

        return fid


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

        self.species = species
        self.chip_name = chip_name

    def read_mapfile(self):
        """Read map data and track informations in memory. Useful to process
        data files"""

        self.mapdata = []

        with open(self.mapfile) as handle:
            # affy files has both " " and "\t" in their files
            for line in handle:
                record = re.split('[ \t]+', line.strip())

                # affy data may have comments in files
                if not record[0].startswith("#"):
                    self.mapdata.append(MapRecord(*record))

    def read_pedfile(self, *args, **kwargs):
        """Open pedfile for reading return iterator"""

        with open(self.pedfile) as handle:
            # affy files has both " " and "\t" in their files
            for record in handle:
                # affy data may have comments in files
                if record.startswith("#"):
                    logger.info(f"Skipping {record}")
                    continue

                line = re.split('[ \t]+', record.strip())

                yield line

    def get_samples(self) -> list:
        """
        Get samples from genotype files

        Returns
        -------
        list
            The sample list.
        """

        sample_list = []

        for line in self.read_pedfile():
            sample_list.append(line[1])

        return sample_list


class AffyPlinkIO(FakePedMixin, TextPlinkIO):
    """a new class for affymetrix plink files, which are slightly different
    from plink text files"""

    def read_pedfile(
            self,
            breed: str = None,
            dataset: Dataset = None,
            *args, **kwargs):
        """
        Open pedfile for reading return iterator

        breed : str, optional
            A breed to be assigned to all samples, or use the sample breed
            stored in database if not provided. The default is None.
        dataset : Dataset, optional
            A dataset in which search for sample breed identifier

        Yields
        ------
        line : list
            A ped line read as a list.
        """

        with open(self.pedfile) as handle:
            # affy files has both " " and "\t" in their files
            for record in handle:
                # affy data may have comments in files
                if record.startswith("#"):
                    logger.info(f"Skipping {record}")
                    continue

                line = re.split('[ \t]+', record.strip())

                if not breed:
                    fid = self.search_fid(line[0], dataset)

                else:
                    fid = breed

                # affy ped lacks of plink columns. add such value to line
                line.insert(0, fid)  # FID
                line.insert(2, '0')  # father
                line.insert(3, '0')  # mother
                line.insert(4, '0')  # SEX
                line.insert(5, '-9')  # phenotype

                yield line

    def get_samples(self) -> list:
        """
        Get samples from genotype files

        Returns
        -------
        list
            The sample list.
        """

        sample_list = []

        with open(self.pedfile) as handle:
            # affy files has both " " and "\t" in their files
            for record in handle:
                # affy data may have comments in files
                if record.startswith("#"):
                    logger.info(f"Skipping {record}")
                    continue

                line = re.split('[ \t]+', record.strip())
                sample_list.append(line[0])

        return sample_list


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

        self.prefix = prefix
        self.species = species
        self.chip_name = chip_name

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: str):
        if prefix:
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

    def read_pedfile(self, *args, **kwargs):
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
                str(int(sample.phenotype))
            ]

            for idx, locus in enumerate(locus_list):
                genotype = snp_arrays[idx][sample_idx]
                line[6+idx*2], line[6+idx*2+1] = convert(genotype, locus)

            yield line

    def get_samples(self) -> list:
        """
        Get samples from genotype files

        Returns
        -------
        list
            The sample list.
        """

        return [sample.iid for sample in self.plink_file.get_samples()]


class IlluminaReportIO(FakePedMixin, SmarterMixin):
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

        self.snpfile = snpfile
        self.report = report
        self.species = species
        self.chip_name = chip_name

    def read_snpfile(self):
        """Read snp data and track informations in memory. Useful to process
        data files"""

        self.mapdata = list(read_snpList(self.snpfile))

    # this will be called when calling read_genotype_method()
    def read_reportfile(
            self,
            breed: str = None,
            dataset: Dataset = None,
            *args, **kwargs):
        """
        Open and read an illumina report file. Returns iterator

        Parameters
        ----------
        breed : str, optional
            A breed to be assigned to all samples, or use the sample breed
            stored in database if not provided. The default is None.
        dataset : Dataset, optional
            A dataset in which search for sample breed identifier

        Raises
        ------
        IlluminaReportException
            Raised when SNPs index doesn't match snpfile.

        Yields
        ------
        line : list
            A ped line read as a list.
        """

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

        # try to returns something like a ped row
        for row in read_illuminaRow(self.report):
            if row.sample_id != last_sample:
                logger.debug(f"Reading sample {row.sample_id}")

                # this is not returned if I'm processing the first sample
                if last_sample:
                    yield line

                # initialize an empty array
                line = ["0"] * size

                if not breed:
                    fid = self.search_fid(row.sample_id, dataset)

                else:
                    fid = breed

                # set values. I need to set a breed code in order to get a
                # proper ped line
                line[0], line[1], line[5] = fid, row.sample_id, "-9"

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

    def get_samples(self) -> list:
        """
        Get samples from genotype files

        Returns
        -------
        list
            The sample list.
        """

        sample_list = []
        last_sample = None

        for row in read_illuminaRow(self.report):
            if row.sample_id != last_sample:
                sample_list.append(row.sample_id)
                last_sample = row.sample_id

        return sample_list


class AffyReportIO(FakePedMixin, SmarterMixin):
    """In this type of file there are both genotypes and informations. Moreover
    genotypes are *transposed*, traking SNP for all samples in a simple line"""

    report = None
    peddata = []
    delimiter = "\t"
    warn_missing_cols = True
    header = []
    n_samples = None

    def __init__(
            self,
            report: str = None,
            species: str = None,
            chip_name: str = None):

        # need to be set in order to write a genotype
        self.read_genotype_method = self.read_peddata

        self.report = report
        self.species = species
        self.chip_name = chip_name

    def __get_header(self):
        # sample names are sanitized through read_affymetrixRow: so read the
        # first header of the report file to determine the original sample
        # names
        with text_or_gzip_open(self.report) as handle:
            position, skipped = skip_comments(handle)

            # go back to header section
            handle.seek(position)

            # now read csv file
            reader = csv.reader(handle, delimiter=self.delimiter)

            # get header
            self.header = next(reader)

    def __warn_missing_column(self, row, columns=[]):
        if self.warn_missing_cols:
            for col in columns:
                if not hasattr(row, col):
                    logger.warning(
                        f"Missing '{col}' column in reportfile!")

    def __process_probeset(self, row, snp_idx):
        # track SNP in mapdata
        try:
            self.mapdata.append(MapRecord(
                row.chr_id, row.probeset_id, 0, row.start))

        except AttributeError as exc:
            logger.debug(exc)
            self.__warn_missing_column(row, ["chr_id", "start"])

            # maybe there are missing columns, try to define a MapRecord
            # with at least probeset id
            self.mapdata.append(MapRecord(
                0, row.probeset_id, 0, 0))

        # track A/B genotype
        try:
            self.genotypes.append(f"{row.allele_a}/{row.allele_b}")

        except AttributeError as exc:
            logger.debug(exc)
            self.__warn_missing_column(row, ["allele_a", "allele_b"])

            # track a missing genotype
            self.genotypes.append("-/-")

        # track genotypes in the proper column (skip the first 6 columns)
        for i in range(self.n_samples):
            call = row[i+1]

            # mind to missing values
            if call == "NoCall":
                logger.debug(
                    f"Skipping SNP {snp_idx}: "
                    f"'{self.mapdata[snp_idx].name}' for sample "
                    f"'{self.header[i+1]}' ({call})")
                continue

            genotype = list(call)
            self.peddata[i][6+snp_idx*2] = genotype[0]
            self.peddata[i][6+snp_idx*2+1] = genotype[1]

    def read_reportfile(self, n_samples: int = None, *args, **kwargs):
        """
        Read reportfile once and generate mapdata and pedata, with genotype
        informations by sample.

        Parameters
        ----------
        n_samples : int, optional
            Limit to N samples. Useful when there are different number of
            samples from reported in file. The default is None (read number
            of samples from reportfile).

        Returns
        -------
        None.
        """

        self.mapdata = []
        self.peddata = []

        if n_samples:
            logger.warning(f"Limiting import to first {n_samples} samples")

        # update samples number with received argument
        self.n_samples = n_samples

        # I want to track also the AB genotypes, to check them while fetching
        # coordinates
        self.genotypes = []

        # those informations are required to define the pedfile
        n_snps = None
        size = None
        initialized = False

        # an index to track SNP accross peddata
        snp_idx = 0

        # warning user once
        self.warn_missing_cols = True

        # try to returns something like a ped row and derive map data in the
        # same time
        for row in read_affymetrixRow(self.report, delimiter=self.delimiter):
            # first determine how many SNPs and samples I have
            if not initialized:
                if not self.n_samples:
                    self.n_samples = row.n_samples

                n_snps = row.n_snps

                # read the original header from report file
                self.__get_header()

                # ok create a ped data object with the required dimensions
                size = 6 + 2 * n_snps
                self.peddata = [["0"] * size for i in range(self.n_samples)]

                # track sample names in row. First column is probeset id
                # read them from the original header row
                for i in range(self.n_samples):
                    self.peddata[i][1] = self.header[i+1]

                # change flag value
                initialized = True

            # deal with a single probeset_id
            self.__process_probeset(row, snp_idx)

            # update SNP column
            snp_idx += 1

            # no more reporting warnings after first row
            self.warn_missing_cols = False

        # check for n of snp after processing reportfile
        if snp_idx != n_snps:
            logger.warning(
                f"Got a different number of SNPs {snp_idx}<>{n_snps}.")

            if snp_idx < n_snps:
                logger.warning("Dropping unused SNPs")

                # determining the proper size
                size = 6 + 2 * snp_idx

                for i, line in enumerate(self.peddata):
                    self.peddata[i] = line[:size]

            else:
                raise AffyReportException(
                    f"Got a different number of SNPs {snp_idx}<>{n_snps}")

    def fetch_coordinates(
            self,
            src_assembly: AssemblyConf,
            dst_assembly: AssemblyConf = None,
            search_field: str = "name",
            chip_name: str = None,
            skip_check: bool = False):
        """Search for variants in smarter database. Check if the provided
        A/B information is equal to the database content

        Args:
            src_assembly (AssemblyConf): the source data assembly version
            dst_assembly (AssemblyConf): the destination data assembly version
            search_field (str): search variant by field (def. "name")
            chip_name (str): limit search to this chip_name
            skip_check (bool): skipp coordinate check
        """

        # call base method
        super().fetch_coordinates(
            src_assembly, dst_assembly, search_field, chip_name)

        # now check that genotypes read from report are equal to src_assembly
        for idx, genotype in enumerate(self.genotypes):
            if idx in self.filtered:
                # this genotype is discared
                continue

            if (not skip_check and
                    genotype != self.src_locations[idx].affymetrix_ab):
                raise AffyReportException(
                    "Genotypes differ from reportfile and src_assembly")

    def read_peddata(
            self,
            breed: str = None,
            dataset: Dataset = None,
            sample_field: str = "original_id",
            *args, **kwargs):
        """
        Yields over genotype record.

        Parameters
        ----------
        breed : str, optional
            A breed to be assigned to all samples, or use the sample breed
            stored in database if not provided. The default is None.
        dataset : Dataset, optional
            A dataset in which search for sample breed identifier
        sample_field : str, optional
            Search samples using this field. The default is "original_id".

        Yields
        ------
        line : list
            A ped line read as a list.
        """

        for line in self.peddata:
            # instantiate a new object in order to be modified
            line = line.copy()

            logger.debug(f"Prepare {line[:10]+ ['...']} to add FID")

            if not breed:
                try:
                    fid = self.search_fid(
                        sample_name=line[1],
                        dataset=dataset,
                        sample_field=sample_field)

                except SmarterDBException as e:
                    logger.debug(e)
                    logger.warning(
                        f"Ignoring sample '{line[1]}': not in database")
                    continue

            else:
                fid = breed

            # set values. I need to set a breed code in order to get a
            # proper ped line
            line[0], line[5] = fid, "-9"

            yield line

    def get_samples(self) -> list:
        """
        Get samples from genotype files

        Returns
        -------
        list
            The sample list.
        """

        sample_list = []

        for line in self.peddata:
            sample_list.append(line[1])

        return sample_list


def plink_binary_exists(prefix: Path):
    "Test if plink binary files exists"

    for ext in [".bed", ".bim", ".fam"]:
        # HINT Path.with_suffix will replace the extension
        test = prefix.parent / (prefix.name + ext)

        if not test.exists():
            return False

    # if I arrive here, all plink binary output files exists
    return True
