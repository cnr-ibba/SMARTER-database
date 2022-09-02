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
from .utils import TqdmToLogger
from .illumina import read_snpList, read_illuminaRow

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
        if species == 'Sheep':
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

    def get_breed(self, fid, dataset, *args, **kwargs):
        """Get breed relying aliases and dataset"""

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

    def get_sample(
            self,
            line: list,
            dataset: Dataset,
            sample_field: str = "original_id"):
        """Get a registered sample from database"""

        # get a breed object from database reling on fid
        breed = self.get_breed(fid=line[0], dataset=dataset)

        # search for sample in database ensure breed are the same
        qs = self.SampleSpecies.objects(
            dataset=dataset,
            breed_code=breed.code,
            **{sample_field: line[1]}
        )

        sex, father_id, mother_id = self._deal_with_relationship(
            line, dataset)

        # this will be the sample I will return
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
            logger.warning(f"Sample '{line[1]}' not found in database")

        else:
            raise SmarterDBException(
                f"Got {qs.count()} results for '{line[1]}'")

        return sample

    def get_or_create_sample(self, line: list, dataset: Dataset, breed: Breed):
        """Get a sample from database or create a new one"""

        # search for sample in database
        qs = self.SampleSpecies.objects(
            original_id=line[1], breed_code=breed.code, dataset=dataset)

        sex, father_id, mother_id = self._deal_with_relationship(
            line, dataset)

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
            # do I have a multi country dataset?
            country = self.get_country(dataset, breed)

            # test if foreground or background dataset
            type_ = get_sample_type(dataset)

            # insert sample into database
            logger.info(f"Registering sample '{line[1]}' in database")
            sample = self.SampleSpecies(
                original_id=line[1],
                country=country,
                species=dataset.species,
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

            # incrementing breed n_individuals counter
            breed.n_individuals += 1
            breed.save()

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
            chip_name: str = None):
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
                logger.warning(
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
                logger.critical(
                    f"Error for SNP {index}:{self.mapdata[index].name}: "
                    f"{a1}/{a2} <> {location.illumina_top}"
                )
                raise CodingException("Not illumina top format")

            # allele coding is the same received as input
            top_genotype = genotype

        elif coding == 'forward':
            if not location.is_forward(genotype):
                logger.critical(
                    f"Error for SNP {index}:{self.mapdata[index].name}: "
                    f"{a1}/{a2} <> {location.illumina_forward}"
                )
                raise CodingException("Not illumina forward format")

            # change the allele coding
            top_genotype = location.forward2top(genotype)

        elif coding == 'ab':
            if not location.is_ab(genotype):
                logger.critical(
                    f"Error for SNP {index}:{self.mapdata[index].name}: "
                    f"{a1}/{a2} <> A/B"
                )
                raise CodingException("Not illumina ab format")

            # change the allele coding
            top_genotype = location.ab2top(genotype)

        elif coding == 'affymetrix':
            if not location.is_affymetrix(genotype):
                logger.critical(
                    f"Error for SNP {index}:{self.mapdata[index].name}: "
                    f"{a1}/{a2} <> {location.affymetrix_ab}"
                )
                raise CodingException("Not affymetrix format")

            # change the allele coding
            top_genotype = location.affy2top(genotype)

        else:
            raise NotImplementedError(f"Coding '{coding}' not supported")

        return top_genotype

    def _process_genotypes(self, line: list, coding: str):
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
            top_genotype = self._to_top(i, genotype, coding, location)

            # replace alleles in ped lines only if necessary
            new_line[6+i*2], new_line[6+i*2+1] = top_genotype

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
            create_samples: bool = False,
            sample_field: str = "original_id"):

        self._check_file_sizes(line)

        logger.debug(f"Processing {line[:10]+ ['...']}")

        # check for breed in database reling on fid.
        try:
            breed = self.get_breed(fid=line[0], dataset=dataset)

        except DoesNotExist as e:
            logger.error(e)
            raise SmarterDBException(
                f"Couldn't find breed_code '{line[0]}': {line[:10]+ ['...']}"
            )

        # check for sample in database
        if create_samples:
            sample = self.get_or_create_sample(line, dataset, breed)

        else:
            sample = self.get_sample(line, dataset, sample_field)

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
        new_line = self._process_genotypes(new_line, coding)

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
        """

        with open(outputfile, "w") as target:
            writer = csv.writer(
                target, delimiter=' ', lineterminator="\n")

            processed = 0

            for line in self.read_genotype_method(
                    dataset=dataset, *args, **kwargs):

                # covert the ped line with the desidered format
                new_line = self._process_pedline(
                    line, dataset, coding, create_samples, sample_field)

                if new_line:
                    # write updated line into updated ped file
                    logger.info(
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

    def get_breed(self, fid, *args, **kwargs):
        """Get breed relying on provided FID and species class attribute"""

        breed = Breed.objects(code=fid, species=self.species).get()

        logger.debug(f"Found breed {breed}")

        return breed


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


class AffyPlinkIO(FakePedMixin, TextPlinkIO):
    """a new class for affymetrix plink files, which are slightly different
    from plink text files"""

    def read_pedfile(self, fid: str, *args, **kwargs):
        """Open pedfile for reading return iterator"""

        with open(self.pedfile) as handle:
            # affy files has both " " and "\t" in their files
            for record in handle:
                # affy data may have comments in files
                if record.startswith("#"):
                    logger.info(f"Skipping {record}")
                    continue

                line = re.split('[ \t]+', record.strip())

                # affy ped lacks of plink columns. add such value to line
                line.insert(0, fid)  # FID
                line.insert(2, '0')  # father
                line.insert(3, '0')  # mother
                line.insert(4, '0')  # SEX
                line.insert(5, -9)  # phenotype

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

        self.prefix = prefix
        self.species = species
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
                int(sample.phenotype)
            ]

            for idx, locus in enumerate(locus_list):
                genotype = snp_arrays[idx][sample_idx]
                line[6+idx*2], line[6+idx*2+1] = convert(genotype, locus)

            yield line


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
            self, fid: str = None, dataset: Dataset = None, *args, **kwargs):
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

                # this is not returned if I'm processing the first sample
                if last_sample:
                    yield line

                # initialize an empty array
                line = ["0"] * size

                logger.debug(f"Searching fid for sample '{row.sample_id}'")

                # determine fid from sample, if not received as argument
                if not fid:
                    try:
                        sample = self.SampleSpecies.objects.get(
                            original_id=row.sample_id,
                            dataset=dataset
                        )

                        breed = sample.breed_code
                        logger.debug(
                            f"Found breed {breed} from {row.sample_id}")

                    except DoesNotExist as e:
                        logger.error(f"Couldn't find {row.sample_id}")
                        raise e
                else:
                    breed = fid

                # set values. I need to set a breed code in order to get a
                # proper ped line
                line[0], line[1], line[5] = breed, row.sample_id, -9

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


def plink_binary_exists(prefix: Path):
    "Test if plink binary files exists"

    for ext in [".bed", ".bim", ".fam"]:
        test = prefix.with_suffix(ext)

        if not test.exists():
            return False

    # if I arrive here, all plink binary output files exists
    return True
