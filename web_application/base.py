#!/usr/bin/env python
from configparser import ConfigParser
from tornado.escape import json_decode, json_encode
from tornado.web import RequestHandler
from psycopg2 import connect

__author__ = 'litleleprikon'


class BaseHandler(RequestHandler):
    def validate(self, validator):
        data = json_decode(self.request.body.decode())
        valid_data = validator.validate(data)
        if valid_data:
            return valid_data
        else:
            self.set_status(403)
            self.finish(json_encode({'status': 'fail', 'message': '\n'.join(validator.get_errors())}))
            return False


class DBConnection:
    _instance = None
    _connection = None

    def get_config(self):
        config = ConfigParser()
        config.read('../config.ini')
        return config['DATABASE']

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            config = self.get_config()
            self._connection = connect(database=config['Database'], user=config['User'], password=config['Password'],
                                       host=config['Host'])
            self._connection.autocommit = True
            self.cursor = self._connection.cursor()
            self.cursor.execute("SET SCHEMA 'project'")

    def __del__(self):
        if self._connection is not None:
            self._connection.close()