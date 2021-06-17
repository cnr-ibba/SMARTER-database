#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 10:54:15 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re
import logging

from lxml import etree as ET

from src.features.utils import text_or_gzip_open

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


def process_rs_elem(elem: ET.Element):
    def clean_tag(tag: str):
        return re.sub(r"\{.*\}", "", tag)

    def recurse_children(snp: dict, path: list, elem: ET.Element):
        for item in elem.iterchildren():
            path.append(clean_tag(item.tag))
            snp = process_element(path, item, snp)
            snp = recurse_children(snp, path, item)
            path.pop()

        return snp

    path = ['ExchangeSet']
    snp = dict()

    # create a snp instance
    path.append(clean_tag(elem.tag))
    snp = process_element(path, elem, snp)

    # iterate over children
    snp = recurse_children(snp, path, elem)

    return snp


def read_dbSNP(path: str):
    with text_or_gzip_open(path, mode="rb") as handle:
        for event, elem in ET.iterparse(handle, events=("end", )):
            tag = re.sub(r"\{.*\}", "", elem.tag)

            if tag.lower() == "rs":
                logger.debug(
                    f"Found tag: {elem.tag}, "
                    f"attrib: {elem.attrib}, text: {str(elem.text).strip()}")
                yield process_rs_elem(elem)

                # release memory after processing elem
                elem.clear()

            else:
                logger.debug(
                    f"Ignoring tag: {elem.tag}, "
                    f"attrib: {elem.attrib}, text: {str(elem.text).strip()}")


def search_chip_snps(snp, handle="AGR_BS"):
    for ss in snp['ss']:
        if ss['handle'] == handle:
            return True
    return False
