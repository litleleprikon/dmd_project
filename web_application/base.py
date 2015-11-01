#!/usr/bin/env python
from tornado.escape import json_decode, json_encode
from tornado.web import RequestHandler

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
