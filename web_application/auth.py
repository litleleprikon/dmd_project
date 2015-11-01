#!/usr/bin/env python
from uuid import uuid4
from tornado import gen
from LIVR.Validator import Validator
from web_application.base import BaseHandler
from zxcvbn import password_strength
from tornado.escape import json_encode
from hashlib import sha512

__author__ = 'litleleprikon'


class StrongPassword(object):
    def __init__(self, *args):
        rule_builders = args[0]

    def __call__(self, value, all_values, output_array):
        if password_strength(value)['score'] < 2:
            return "WEAK_PASSWORD"

Validator.register_default_rules({'strong_pass': StrongPassword})

CREATE_USER_VALIDATOR = Validator({
    'username': ['required', {'length_between': [6, 50]}],
    'password': ['required', {'min_length': 6}, 'strong_pass'],
    'email': ['required', 'email']
})

LOGIN_VALIDATOR = Validator({
    'username': 'required',
    'password': 'required'
})


class AuthReqHandler(BaseHandler):
    def get_current_user(self):
        sid = self.get_secure_cookie('sid')
        cursor = self.application.db.execute('SELECT uid FROM project.sessions WHERE sid = %s', sid)
        return cursor.fetchone()[0]


class UserHandler(BaseHandler):
    SUPPORTED_METHODS = ("POST", "PUT")

    @gen.coroutine
    def post(self):
        valid_data = self.validate(CREATE_USER_VALIDATOR)
        if not valid_data:
            return
        user_exists = yield self.application.db.execute(
            'SELECT EXISTS (SELECT TRUE FROM project."user" WHERE username=%s);',
            [valid_data['username']]
        )
        if user_exists.fetchone()[0]:
            self.set_status(409)
            self.finish(json_encode({'status': 'fail', 'message': 'User with this username already exist'}))
        salt = uuid4().hex
        pass_hash = sha512(valid_data['password'].encode() + salt.encode()).hexdigest()
        cursor = yield self.application.db.execute('''
            INSERT INTO project.user (username, passhash, salt, email)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', [valid_data['username'], pass_hash, salt, valid_data['email']])
        uid = cursor.fetchone()[0]
        self.finish(json_encode({'status': 'success', 'message': 'User created', 'id': uid}))


class LoginHandler(BaseHandler):
    SUPPORTED_METHODS = ('POST', 'DELETE')

    @gen.coroutine
    def post(self):
        valid_data = self.validate(LOGIN_VALIDATOR)
        if not valid_data:
            return
        cursor = yield self.application.db.execute('SELECT id, passhash, salt FROM project."user" WHERE username = %s',
                                             [valid_data['username']])
        if cursor.rowcount == 0:
            self.set_status(400)
            self.finish(json_encode({'status': 'fail', 'message': 'No such user'}))
            return
        user_id, pass_hash, salt = cursor.fetchone()
        if sha512(valid_data['password'].encode() + salt.encode()).hexdigest() != pass_hash:
            self.set_status(400)
            self.finish(json_encode({'status': 'fail', 'message': 'Incorrect password'}))
            return
        sid = uuid4().hex
        cursor = yield self.application.db.execute(
            'INSERT INTO project.sessions (sid, uid) VALUES (%s, %s)',
            [sid, user_id])
        self.set_secure_cookie('sid', sid)
        self.finish(json_encode({'status': 'success', 'message': 'Login successful'}))

