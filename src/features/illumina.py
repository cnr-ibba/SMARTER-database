#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 17:15:26 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re
import csv
import datetime
import logging
import collections
from typing import Tuple

import Bio.Seq

from typing import Union
from dateutil.parser import parse as parse_date

from src.features.utils import sanitize, text_or_gzip_open

# Get an instance of a logger
logger = logging.getLogger(__name__)

# the desidered SNP pattern
SNP_PATTERN = re.compile(r"\[([acgt]/[acgt])\]", re.IGNORECASE)


class IlluSNPException(Exception):
    """Base exception class for IlluSNP"""

    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)


def skip_lines(handle, skip) -> Tuple[int, list]:
    logger.info(f"Skipping {skip} lines")

    # track skipped lines
    skipped = list()

    for i in range(skip):
        line = handle.readline().strip()
        position = handle.tell()

        logger.warning(f"Skipping: {line}")
        skipped.append(line)

    return position, skipped


def skip_until_section(handle, section) -> Tuple[int, list]:
    """Ignore lines until a precise sections"""

    # track skipped lines
    skipped = list()

    # search for 'section' record
    while True:
        line = handle.readline().strip()
        position = handle.tell()

        logger.warning(f"Skipping: {line}")
        skipped.append(line)

        # last skipped line is included in skipped array
        if section in line:
            break

    return position, skipped


def search_manifactured_date(header: list) -> Union[datetime.datetime, None]:
    """Grep manifactured date from illumina header

    Args:
        header (list): the illumina header skipped lines
    Returns:
        datetime.datetime: a datetime object
    """

    records = list(filter(lambda record: 'date' in record.lower(), header))

    date = None

    if records:
        record = records[0].split(",")
        date = parse_date(record[1])

    return date


def sniff_file(handle, size, position=0):
    sniffer = csv.Sniffer()

    # try to determine dialect
    try:
        data = handle.read(size)
        dialect = sniffer.sniff(data)

    except csv.Error as e:
        logger.error(e)
        logger.error(data)
        raise e

    handle.seek(position)
    return csv.reader(handle, dialect=dialect)


def read_snpMap(path: str, size=2048, skip=0, delimiter=None):
    with open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)

        else:
            if skip > 0:
                skip_lines(handle, skip)

            # try to determine dialect
            reader = sniff_file(handle, size)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        # define a datatype for my data
        SnpMap = collections.namedtuple("SnpMap", header)

        # add records to data
        for record in reader:
            # forcing data types
            record[header.index('index')] = int(
                record[header.index('index')])

            record[header.index('position')] = int(
                record[header.index('position')])

            record[header.index('gentrain_score')] = float(
                record[header.index('gentrain_score')])

            record[header.index('normid')] = int(
                record[header.index('normid')])

            # convert into collection
            record = SnpMap._make(record)
            yield record


def read_Manifest(path: str, size=2048, skip=0, delimiter=None):
    with text_or_gzip_open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)
            _, skipped = skip_until_section(handle, "[Assay]")

        else:
            if skip > 0:
                position, skipped = skip_lines(handle, skip)

            else:
                # search for [Assay] row
                position, skipped = skip_until_section(handle, "[Assay]")

            # try to determine dialect
            reader = sniff_file(handle, size, position)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        # ok try to get the manifatcured date
        date = search_manifactured_date(skipped)

        # add date to header
        header.append("date")

        logger.info(header)

        # define a datatype for my data
        SnpChip = collections.namedtuple("SnpChip", header)

        # add records to data
        for record in reader:
            # break after assay section
            if record[0] == '[Controls]':
                logger.debug("[Assay] section processed")
                break

            # add date to record
            record.append(date)

            # forcing data types
            try:
                record[header.index('mapinfo')] = int(
                    record[header.index('mapinfo')])

            except ValueError as e:
                logging.warning(
                    "Cannot parse %s:%s" % (record, str(e)))

            # check that record is not an indel
            sequence = record[header.index('sourceseq')]
            match = re.search(SNP_PATTERN, sequence)

            if match is None:
                logger.warning(
                    "Can't find a SNP in %s. No indels and only 2 "
                    "allelic SNPs are supported" % (sequence))

                # in this case, skip this record
                logger.warning(f"Skipping {record[header.index('name')]}")
                continue

            # drop brakets from SNP [A/G] -> A/G
            record[header.index('snp')] = re.sub(
                r'[\[\]]',
                "",
                record[header.index('snp')])

            # convert into collection
            record = SnpChip._make(record)
            yield record


def read_snpList(path: str, size=2048, skip=0, delimiter=None):
    with text_or_gzip_open(path) as handle:
        if delimiter:
            reader = csv.reader(handle, delimiter=delimiter)

        else:
            if skip > 0:
                skip_lines(handle, skip)

            # try to determine dialect
            reader = sniff_file(handle, size)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        logger.info(header)

        # define a datatype for my data
        SnpList = collections.namedtuple("SnpList", header)

        # add records to data
        for record in reader:
            # forcing data types
            if 'index' in header:
                # this column could be present or not
                record[header.index('index')] = int(
                    record[header.index('index')])

            record[header.index('position')] = int(
                record[header.index('position')])

            if 'snp' in header:
                # drop brakets from SNP [A/G] -> A/G
                record[header.index('snp')] = re.sub(
                    r'[\[\]]',
                    "",
                    record[header.index('snp')])

            # convert into collection
            record = SnpList._make(record)
            yield record


def read_illuminaRow(path: str, size=2048):
    with text_or_gzip_open(path) as handle:
        # search for [DATA] record
        position, skipped = skip_until_section(handle, "[Data]")

        # try to determine dialect
        reader = sniff_file(handle, size, position)

        # get header
        header = next(reader)

        # sanitize column names
        header = [sanitize(column) for column in header]

        # define a datatype for my data
        IlluminaRow = collections.namedtuple("IlluminaRow", header)

        # add records to data
        for i, record in enumerate(reader):
            # convert into collection
            try:
                record = IlluminaRow._make(record)
                yield record

            except TypeError as exc:
                raise IlluSNPException(
                    f"Error for line {i+len(skipped)+1}:{record}: {exc}. ")


class IlluSNP():
    def __init__(self, sequence=None, max_iter=10):
        """Define a IlluSNP class"""

        self.sequence = None
        self.strand = None
        self.A = None
        self.B = None
        self.alleles = None
        self.illumina = None
        self.max_iter = None
        self.pos = None

        if sequence is not None:
            self.fromSequence(sequence, max_iter=max_iter)

    def __repr__(self):
        """Return a string"""

        return (f"<{self.__module__}.IlluSNP(sequence='{self.sequence}', "
                f"illumina='{self.illumina}', alleles='{self.alleles}, "
                f"strand='{self.strand}', A='{self.A}', B='{self.B}')>")

    def __eq__(self, other):
        """Test equality"""

        t1 = (self.sequence, self.strand, self.A, self.B, self.alleles)
        t2 = (other.sequence, other.strand, other.A, other.B, other.alleles)

        return t1 == t2

    def __ne__(self, other):
        """test not equality"""

        t1 = (self.sequence, self.strand, self.A, self.B, self.alleles)
        t2 = (other.sequence, other.strand, other.A, other.B, other.alleles)

        return t1 != t2

    def fromSequence(self, sequence, max_iter=10):
        """Define a IlluSNP from a sequence"""

        # mind to lower letters. Transform sequence in capital letters
        sequence = sequence.upper()

        # call findSNP
        snp, pos = self.findSNP(sequence)

        # is snp unambiguous?
        if self.isUnambiguous(snp):
            self.A, self.B, self.strand = self._setABsnp(snp)

        else:
            # When snp is ambiguous, the actual SNP is
            # considered to be position ‘n’. The sequences immediately
            # before and after the SNP is evaluated

            # get flanking sequence. mind [] around SNP positions
            for n in range(1, max_iter+1):
                # pos is a tuple of indices, like (10, 15). The stop position
                # is not included
                try:
                    pair = "%s/%s" % (sequence[pos[0]-n], sequence[pos[1]+n-1])

                except IndexError as exc:
                    logger.error(exc)
                    raise IlluSNPException(
                        "Can't find unambiguous pair, max_iter exceed "
                        "sequence length"
                    )

                logger.debug("Step %s: considering pair %s" % (n, pair))

                if self.isUnambiguous(pair):
                    self.A, self.B, self.strand = self._setABpair(pair, snp)

                    # leave cicle
                    break

            if n == max_iter and not self.isUnambiguous(pair):
                raise IlluSNPException(
                    "Can't find unambiguous pair in %s "
                    "steps (%s)" % (max_iter, sequence))

        # assign values
        self.sequence = sequence
        self.alleles = snp
        self.illumina = f"{self.A}/{self.B}"
        self.max_iter = max_iter
        self.pos = pos

    def _setABsnp(self, snp):
        """Set strand and A/B alleles for unambiguous SNP"""

        # get strand assignment
        alleles = snp.split("/")
        strand = None
        A = None
        B = None

        # The simplest case of determining strand and allele designations
        # occurs when one of the possible variations of the SNP
        # is an adenine (A), and the remaining variation is either a
        # cytosine (C) or guanine (G). In this instance, the sequence
        # for this SNP is designated TOP, and the A nucleotide is designated
        # Allele A. Therefore, the C or G is Allele B. For more information:
        # https://www.illumina.com/documents/products/technotes/technote_topbot.pdf
        if "A" in alleles:
            strand = "TOP"

            if alleles.index("A") == 0:
                A, B = alleles

            else:
                B, A = alleles

            logger.debug(
                "Found A. Set strand = '%s', A = '%s' B = '%s'" % (
                    strand, A, B))

        # when one of the possible variations of the SNP is a thymine (T),
        # and the remaining variation is either a C or a G, the
        # sequence for this SNP is designated BOT and the T
        # nucleotide is designated Allele A. The C or the G
        # nucleotide is Allele B. For more information:
        # https://www.illumina.com/documents/products/technotes/technote_topbot.pdf
        elif "T" in alleles:
            strand = "BOT"

            if alleles.index("T") == 0:
                A, B = alleles

            else:
                B, A = alleles

            logger.debug(
                "Found T. Set strand = '%s', A = '%s' B = '%s'" % (
                    strand, A, B))

        return A, B, strand

    def _setABpair(self, pair, snp):
        """Set strand and A/B alleles for unambiguous pair"""

        pair = pair.split("/")
        alleles = snp.split("/")
        strand = None
        A = None
        B = None

        # To designate Strand, when the A or T in the first
        # unambiguous pair is on the 5’ side of the SNP, then the
        # sequence is designated TOP. To designate Allele for an [A/T] SNP,
        # when the Strand is TOP then Allele A = A and Allele B = T.
        # To designate Allele for a [C/G] SNP, when the Strand is
        # TOP then Allele A = C and Allele B = G.
        if "A" in pair[0] or "T" in pair[0]:
            strand = "TOP"
            A, B = alleles

            logger.debug(
                "Found %s in 5'. Set strand = '%s', A = '%s' "
                "B = '%s'" % (pair[0], strand, A, B))

        # When the A or T in the first
        # unambiguous pair is on the 3’ side of the SNP, then the
        # sequence is designated BOT. To designate Allele for an [A/T] SNP,
        # when the strand is BOT, then Allele A = T and Allele B = A.
        # To designate Allele for a [C/G] SNP, when the Strand is
        # BOT then Allele A = G and Allele B = C.
        else:
            strand = "BOT"
            B, A, = alleles

            logger.debug(
                "Found %s in 3'. Set strand = '%s', A = '%s' "
                "B = '%s'" % (pair[1], strand, A, B))

        return A, B, strand

    def findSNP(self, sequence):
        """Find snp (eg [A/G] in sequence (0-based)"""

        logger.debug(f"Got '{sequence}' as sequence")

        match = re.search(SNP_PATTERN, sequence)

        if match is None:
            raise IlluSNPException(
                "Can't find a SNP in %s. No indels and only 2 "
                "allelic SNPs are supported" % (sequence))

        # get SNP and position. Capitalize SNP
        snp = match.groups()[0].upper()
        position = match.span()

        logger.debug("Found %s in position %s" % (snp, position))

        return snp, position

    def isUnambiguous(self, snp):
        """Return True if snp is unambiguous"""

        # split snp by separator
        alleles = snp.split("/")

        # test for alleles length
        if len(alleles) != 2:
            raise IlluSNPException(
                "Too many alleles in %s "
                "Can only deal with 'A/B' snps" % (alleles))

        # check for ambigousity. Only two snps considered
        if "A" in alleles or "T" in alleles:
            if "C" in alleles or "G" in alleles:
                logger.debug("%s is unambiguous" % (snp))
                return True

        # default value
        logger.debug("%s is ambiguous" % (snp))
        return False

    def toTop(self):
        """Convert a BOT sequence into TOP"""

        logger.debug("Convert SNP into illumina top")

        if self.strand == "TOP":
            return self

        # create a copy of the sequence without SNP
        sequence = self.sequence.replace(f"[{self.alleles}]", '')

        # get reverse complement of the sequence
        reverse = Bio.Seq.MutableSeq(sequence)
        reverse.reverse_complement(inplace=True)

        # mind to complement the SNP
        snp = Bio.Seq.MutableSeq(self.illumina)
        snp.complement(inplace=True)
        snp = "/".join(str(snp).split("/"))

        # insert SNP into sequence
        # mind that where flanking sequences are different in length
        # the position I have is relative to the end
        tmp = list(f"[{snp}]")
        tmp.reverse()

        for i, char in enumerate(tmp):
            reverse.insert(-self.pos[0]-i, char)

        # convert into string, return a IlluSNP object
        return IlluSNP(str(reverse), max_iter=self.max_iter)
