#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 10:54:15 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re
import gzip
import logging

from lxml import etree as ET

# Get an instance of a logger
logger = logging.getLogger(__name__)


def process_element(path: list, elem: ET.Element, snp: dict):
    if path == ['ExchangeSet', 'Rs']:
        logger.debug(f"Creating a new SNP: {elem.attrib}")
        snp = dict(elem.attrib)

    elif path == ['ExchangeSet', 'Rs', 'Create']:
        logger.debug(f"Update snp: {elem.attrib}")
        snp["create"] = dict(elem.attrib)

    elif path == ['ExchangeSet', 'Rs', 'Update']:
        logger.debug(f"Update snp: {elem.attrib}")
        snp["update"] = dict(elem.attrib)

    elif path == ['ExchangeSet', 'Rs', 'Sequence']:
        logger.debug(f"Create exemplar: {elem.attrib}")
        snp["exemplar"] = dict(elem.attrib)

    elif path == ['ExchangeSet', 'Rs', 'Sequence', 'Observed']:
        logger.debug(f"Update exemplar: {elem.text.strip()}")
        snp["exemplar"]["observed"] = elem.text.strip()

    elif path == ['ExchangeSet', 'Rs', 'Ss']:
        if 'ss' in snp:
            logger.debug(f"Update snp. Append ss: {elem.attrib}")
            snp["ss"].append(dict(elem.attrib))
        else:
            logger.debug(f"Update snp. Create ss: {elem.attrib}")
            snp["ss"] = [dict(elem.attrib)]

    elif path == ['ExchangeSet', 'Rs', 'Ss', 'Sequence', 'Seq5']:
        logger.debug(f"Update seq5 for ss {snp['ss'][-1]['ssId']}")
        snp["ss"][-1]["seq5"] = elem.text.strip()

    elif path == ['ExchangeSet', 'Rs', 'Ss', 'Sequence', 'Observed']:
        logger.debug(f"Update observed for ss {snp['ss'][-1]['ssId']}")
        snp["ss"][-1]["observed"] = elem.text.strip()

    elif path == ['ExchangeSet', 'Rs', 'Ss', 'Sequence', 'Seq3']:
        logger.debug(f"Update seq3 for ss {snp['ss'][-1]['ssId']}")
        snp["ss"][-1]["seq3"] = elem.text.strip()

    elif path == ['ExchangeSet', 'Rs', 'Assembly']:
        logger.debug(f"Adding assembly record: {elem.attrib}")
        snp["assembly"] = dict(elem.attrib)

    elif path == ['ExchangeSet', 'Rs', 'Assembly', 'Component']:
        logger.debug(f"Update assembly record: {elem.attrib}")
        snp["assembly"]["component"] = dict(elem.attrib)

    elif path == ['ExchangeSet', 'Rs', 'Assembly', 'Component', 'MapLoc']:
        logger.debug(f"Update assembly record: {elem.attrib}")
        snp["assembly"]["component"]["maploc"] = dict(elem.attrib)

    elif path == ['ExchangeSet', 'Rs', 'Assembly', 'SnpStat']:
        logger.debug(f"Update assembly record: {elem.attrib}")
        snp["assembly"]["snpstat"] = dict(elem.attrib)

    else:
        logger.debug(
            f"Ignoring '{path}': {elem.attrib}, {str(elem.text).strip()}")

    return snp


def read_dbSNP(path: str):
    keys = list()
    snp = dict()

    with gzip.open(path) as handle:
        for event, elem in ET.iterparse(
                handle,
                events=("start", "end")):

            logger.debug(
                f"event: {event}, tag: {elem.tag}, "
                f"attrib: {elem.attrib}, text: {elem.text}")

            tag = re.sub(r"\{.*\}", "", elem.tag)

            if event == "start":
                # appending tag to the path keys
                keys.append(tag)

                logger.debug(
                    f"Got {event} event for '{tag}'. Keys are: {keys}")

                # processing element
                try:
                    snp = process_element(keys, elem, snp)

                except AttributeError as e:
                    logger.error(
                        f"Error while reading {keys} "
                        f"for rs{snp['rsId']}: {e}")

            elif event == "end":
                # remove last elemenent from path keys
                key = keys.pop()

                if key != tag:
                    raise Exception(
                        f"Remove a key different from last tag {key}<>{tag}")

                logger.debug(
                    f"Got {event} event for '{key}'. Keys are: {keys}")

                # debug
                if key == "Rs":
                    logger.debug(f"Found rsID {snp['rsId']}")
                    yield snp

                    # reset snp
                    snp = dict()

                # release memory after processing elem
                elem.clear()

            # case event

        # cicle elementtree

    # closing file


def search_chip_snps(snp, handle="AGR_BS"):
    for ss in snp['ss']:
        if ss['handle'] == handle:
            return True
    return False
