#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 18:07:13 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import logging

from pathlib import Path
from functools import partial

from dotenv import find_dotenv, load_dotenv
from mongoengine import MultipleObjectsReturned
from pymongo import MongoClient

from src.features.smarterdb import global_connection, VariantSheep, SMARTERDB
from src.features.dbsnp import read_dbSNP, search_chip_snps

search_agr_bs = partial(search_chip_snps, handle='AGR_BS')


def main():
    logger = logging.getLogger(__name__)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    dbsnp_file = (
        "data/external/SHE/dbSNP/ds_ch24.xml.gz")
    dbsnp_path = project_dir / dbsnp_file

    # connect to database
    global_connection()

    # connect to database
    conn = MongoClient(
        'mongodb://localhost:27017/',
        username=os.getenv("MONGODB_SMARTER_USER"),
        password=os.getenv("MONGODB_SMARTER_PASS")
    )

    # get my snp names from database
    pipeline = [
        {"$project": {"_id": 0, "name": 1}},
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "items": {"$push": "$name"}
        }}
    ]

    logger.info("Search all names in database")

    # execute the aggregation pipeline with pymongo client and get all
    # snp names from database
    result = next(conn[SMARTERDB]["variantSheep"].aggregate(pipeline))

    # get all names in a set
    all_snp_names = set(result["items"])

    logger.info(f"Reading from {dbsnp_path}")

    # cicle amoung dbsnp object
    for snp in filter(search_agr_bs, read_dbSNP(dbsnp_path)):
        found = False

        for i, ss in enumerate(snp["ss"]):
            if ss['locSnpId'] in all_snp_names:
                found = True
                break

        if found is False:
            logger.debug(f"Skipping rsId {snp['rsId']}")
            continue

        snp['ss'] = snp['ss'][i]

        # get the locSnpId to search (ex. OAR24_20639954
        name = snp['ss']['locSnpId']

        # regex is super slow
        qs = VariantSheep.objects(name=name)

        if qs.count() > 0:
            # get variant
            try:
                variant = qs.get()
                logger.info(f"{variant}: {snp}")

            except MultipleObjectsReturned:
                logger.error(qs.all())

            # debug
            break

    logger.info("Completed")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logging.getLogger('src.features.dbsnp').setLevel(logging.INFO)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
