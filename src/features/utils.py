#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 14:13:51 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import io
import re
import logging
import pathlib

# Get an instance of a logger
logger = logging.getLogger(__name__)


def sanitize(word: str, chars=['.', ","], check_mongoengine=True) -> str:
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

    if sanitized in ['size', 'type']:
        sanitized += "_"

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
