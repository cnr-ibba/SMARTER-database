#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 14:13:51 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import re


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
