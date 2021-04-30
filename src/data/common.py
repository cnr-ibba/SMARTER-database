#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 15:13:32 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Common stuff for smarter scripts
"""

import logging

from pathlib import Path

from src.features.smarterdb import Dataset

# Get an instance of a logger
logger = logging.getLogger(__name__)


def fetch_and_check_dataset(
        archive: str, contents: list[str]) -> [Dataset, list[Path]]:
    """Common operations on dataset: fetch a dataset by file (submitted
    archive), check that working dir exists and required file contents is
    in dataset. Test and get full path of required files

    Args:
        archive (str): the dataset archive (file)
        contents (list): a list of files which beed to be defined in dataset

    Returns:
        Dataset: a dataset instance
        list[Path]: a list of Path of required files
    """

    # get the dataset object
    dataset = Dataset.objects(file=archive).get()

    logger.debug(f"Found {dataset}")

    # check for working directory
    working_dir = dataset.working_dir

    if not working_dir.exists():
        raise FileNotFoundError(
            f"Could find dataset directory '{working_dir}'")

    # check files are in dataset
    not_found = []
    contents_path = []

    for item in contents:
        if item not in dataset.contents:
            logger.error(f"Couldn't find '{item}' in dataset: '{dataset}'")
            not_found.append(item)
            continue

        item_path = working_dir / item

        if not item_path.exists():
            logger.error(
                f"Couldn't find '{item_path}' in dir: '{working_dir}'")
            not_found.append(item)
            continue

        contents_path.append(item_path)

    if len(not_found) > 0:
        raise FileNotFoundError(
            f"Couldn't find '{not_found}'")

    return dataset, contents_path
