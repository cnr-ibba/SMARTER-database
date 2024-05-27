#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 14:13:51 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import io
import re
import gzip
import logging
import pathlib
import collections
from typing import Tuple, List

from pycountry import countries

# Get an instance of a logger
logger = logging.getLogger(__name__)

# manage custom countries
# english name for turkey
countries.add_entry(
    alpha_2="TR", alpha_3="TUR", name="Turkey", numeric="792",
    official_name='Republic of Türkiye')


def sanitize(
        word: str,
        chars=['.', ",", "-", "/", "#"],
        check_mongoengine=True) -> str:
    """Sanitize a word by removing unwanted characters and lowercase it.

    Args:
        word (str): the word to sanitize
        chars (list): a list of characters to remove
        check_mongoengine (bool): true to add '_' after a mongoengine reserved
            word

    Returns:
        str: the sanitized word
    """

    # remove unwanted characters from word by putting spaces
    pattern = "".join(chars)
    tmp = re.sub(r'[%s]' % (pattern), ' ', word)

    # remove spaces from column name and lowercase all
    sanitized = re.sub(r"\s+", "_", tmp).lower()

    if check_mongoengine:
        if sanitized in ['size', 'type']:
            sanitized += "_"

    # remove starting sanitized char (can't be used with namedtuple)
    if sanitized.startswith("_"):
        sanitized = sanitized[1:]

    return sanitized


def camelCase(string: str) -> str:
    """Convert a string into camel case

    Args:
        string (str): the string to convert

    Returns:
        str: the camel case version of the string
    """

    string = re.sub(r"(_|-|\.)+", " ", string).title().replace(" ", "")
    return string[0].lower() + string[1:]


class TqdmToLogger(io.StringIO):
    """
        Output stream for TQDM which will output to logger module instead of
        the StdOut.
    """
    logger = None
    level = None
    buf = ''

    def __init__(self, logger, level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or logging.INFO

    def write(self, buf):
        self.buf = buf.strip('\r\n\t ')

    def flush(self):
        self.logger.log(self.level, self.buf)


def get_project_dir() -> pathlib.PosixPath:
    """Return smarter project dir (which are three levels upper from the
    module in which this function is stored)

    Returns:
        pathlib.PosixPath: the smarter project base dir
    """
    return pathlib.Path(__file__).parents[2]


def get_raw_dir() -> pathlib.PosixPath:
    """Return smarter data raw dir

    Returns:
        pathlib.PosixPath: the smarter data raw directory
    """

    return get_project_dir() / "data/raw"


def get_interim_dir() -> pathlib.PosixPath:
    """Return smarter data temporary dir

    Returns:
        pathlib.PosixPath: the smarter data temporary dir
    """

    return get_project_dir() / "data/interim"


def get_processed_dir() -> pathlib.PosixPath:
    """Return smarter data processed dir (final processed data)

    Returns:
        pathlib.PosixPath: the smarter data final processed dir
    """

    return get_project_dir() / "data/processed"


def text_or_gzip_open(path: str, mode: str = None) -> io.TextIOWrapper:
    """Open a file which can be compressed or not. Returns file handle"""

    if pathlib.Path(path).suffix == '.gz':
        if not mode:
            mode = 'rt'

        logger.debug(f"Gzip detected for {path}")
        return gzip.open(path, mode=mode)

    else:
        if not mode:
            mode = 'r'

        return open(path, mode=mode)


def find_duplicates(header: list) -> list:
    """Find duplicate columns in list. Returns index to remove after the first
    occurence

    Args:
        header (list): a list like the header read from a CSV file

    Returns:
        list: a list of index (numeric)
    """

    to_remove = []

    # count columns and find duplicates
    counts = collections.Counter(header)
    duplicated_cols = [key for key, value in counts.items() if value > 1]

    # now iterate and get duplicates indexes
    for duplicated in duplicated_cols:
        # get all duplicated index
        tmp = [i for i, col in enumerate(header) if col == duplicated]

        # track only from the 2nd occurrence
        to_remove += tmp[1:]

    return to_remove


def skip_comments(
        handle: io.TextIOWrapper, comment_char="#") -> Tuple[int, List[str]]:
    """
    Ignore comments lines from a open file handle. Return the stream position
    immediately after the comments and all the comment lines in a list.

    Parameters
    ----------
    handle : io.TextIOWrapper
        An open file handle.
    comment_char : TYPE, optional
        The comment character used in file. The default is "#".

    Returns
    -------
    Tuple[int, List[str]]
        The stream position after the comments and the ignored lines as a list.
    """

    # track skipped lines
    skipped = list()

    # read first line
    line = handle.readline().strip()

    # search for comments in file
    while line[0] == "#":
        logger.debug(f"Skipping: {line}")
        skipped.append(line)
        position = handle.tell()

        # read another line
        line = handle.readline().strip()

    # the position returned is the one before the one I want
    return position, skipped


class UnknownCountry():
    """Deal with unknown country"""

    def __init__(self):
        self.name = "Unknown"
        self.alpha_2 = "UN"
        self.alpha_3 = "UNK"
        self.numeric = None
