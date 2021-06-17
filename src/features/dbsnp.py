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


class DBSNP():
    config = {
        ('ExchangeSet', 'Rs', 'Create'): "record_create",
        ('ExchangeSet', 'Rs', 'Update'): "record_update",
        ('ExchangeSet', 'Rs', 'Sequence'): "record_exemplar",
        ('ExchangeSet', 'Rs', 'Sequence', 'Observed'): "record_observed",
        ('ExchangeSet', 'Rs', 'Ss'): "record_ss",
        ('ExchangeSet', 'Rs', 'Ss', 'Sequence', 'Seq5'): "ss_seq5",
        ('ExchangeSet', 'Rs', 'Ss', 'Sequence', 'Observed'): "ss_observed",
        ('ExchangeSet', 'Rs', 'Ss', 'Sequence', 'Seq3'): "ss_seq3",
        ('ExchangeSet', 'Rs', 'Assembly'): "record_assembly",
        ('ExchangeSet', 'Rs', 'Assembly', 'Component'): 'ass_component',
        ('ExchangeSet', 'Rs', 'Assembly', 'Component', 'MapLoc'): 'ass_maploc',
        ('ExchangeSet', 'Rs', 'Assembly', 'SnpStat'): 'ass_snpstat',
    }

    def __init__(self, path, elem):
        logger.debug(f"Creating a new SNP: {elem.attrib}")
        self.snp = dict(elem.attrib)

    @classmethod
    def clean_tag(cls, tag: str):
        return re.sub(r"\{.*\}", "", tag)

    def to_dict(self):
        return self.snp

    def recurse_children(self, path: list, elem: ET.Element):
        for item in elem.iterchildren():
            path.append(self.clean_tag(item.tag))
            self.process_element(path, item)
            self.recurse_children(path, item)
            path.pop()

    def process_element(self, path, elem):
        path = tuple(path)

        if path in self.config:
            func = self.config[path]
            func = getattr(self, func)
            func(elem)

        else:
            logger.warning(
                f"Ignoring '{path}': {elem.attrib}, {str(elem.text).strip()}")

    def record_create(self, elem):
        logger.debug(f"Update snp: {elem.attrib}")
        self.snp["create"] = dict(elem.attrib)

    def record_update(self, elem):
        logger.debug(f"Update snp: {elem.attrib}")
        self.snp["update"] = dict(elem.attrib)

    def record_exemplar(self, elem):
        logger.debug(f"Create exemplar: {elem.attrib}")
        self.snp["exemplar"] = dict(elem.attrib)

    def record_observed(self, elem):
        logger.debug(f"Update exemplar: {elem.text.strip()}")
        self.snp["exemplar"]["observed"] = elem.text.strip()

    def record_ss(self, elem):
        if 'ss' in self.snp:
            logger.debug(f"Update snp. Append ss: {elem.attrib}")
            self.snp["ss"].append(dict(elem.attrib))
        else:
            logger.debug(f"Update snp. Create ss: {elem.attrib}")
            self.snp["ss"] = [dict(elem.attrib)]

    def ss_seq5(self, elem):
        logger.debug(f"Update seq5 for ss {self.snp['ss'][-1]['ssId']}")
        self.snp["ss"][-1]["seq5"] = elem.text.strip()

    def ss_observed(self, elem):
        logger.debug(f"Update observed for ss {self.snp['ss'][-1]['ssId']}")
        self.snp["ss"][-1]["observed"] = elem.text.strip()

    def ss_seq3(self, elem):
        logger.debug(f"Update seq3 for ss {self.snp['ss'][-1]['ssId']}")
        self.snp["ss"][-1]["seq3"] = elem.text.strip()

    def record_assembly(self, elem):
        logger.debug(f"Adding assembly record: {elem.attrib}")
        self.snp["assembly"] = dict(elem.attrib)

    def ass_component(self, elem):
        logger.debug(f"Update assembly record: {elem.attrib}")
        self.snp["assembly"]["component"] = dict(elem.attrib)

    def ass_maploc(self, elem):
        logger.debug(f"Update assembly record: {elem.attrib}")
        self.snp["assembly"]["component"]["maploc"] = dict(elem.attrib)

    def ass_snpstat(self, elem):
        logger.debug(f"Update assembly record: {elem.attrib}")
        self.snp["assembly"]["snpstat"] = dict(elem.attrib)


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


def process_rs_elem_new(elem: ET.Element):
    # initialize path
    path = ['ExchangeSet']

    # create a snp instance. Add first tag to path
    path.append(DBSNP.clean_tag(elem.tag))
    snp = DBSNP(path, elem)

    # iterate over children
    snp.recurse_children(path, elem)

    return snp.to_dict()


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


def read_dbSNP_new(path: str):
    with text_or_gzip_open(path, mode="rb") as handle:
        for event, elem in ET.iterparse(handle, events=("end", )):
            tag = re.sub(r"\{.*\}", "", elem.tag)

            if tag.lower() == "rs":
                logger.debug(
                    f"Found tag: {elem.tag}, "
                    f"attrib: {elem.attrib}, text: {str(elem.text).strip()}")
                yield process_rs_elem_new(elem)

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
