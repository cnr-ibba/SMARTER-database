#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 17:44:00 2021

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

from mongoengine import connect, disconnect, connection

from src.features.smarterdb import DB_ALIAS


class MongoMockMixin():
    @classmethod
    def setUpClass(cls):
        connect(
            'mongoenginetest',
            host='mongomock://localhost',
            alias=DB_ALIAS)

        cls.connection = connection.get_db(alias=DB_ALIAS)

    @classmethod
    def tearDownClass(cls):
        disconnect()
