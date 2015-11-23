#!/usr/bin/env python
import json
from uuid import uuid4
from aiohttp import web
from LIVR.Validator import Validator
import re
from hashlib import sha512

from web_application.base import validate

__author__ = 'litleleprikon'

STRONG_PASS_RE = re.compile(r'(?=^.{8,}$)(?=.*\d)(?=.*[!@#$%^&*]+)(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$')


class StrongPassword(object):
    def __init__(self, *args):
        rule_builders = args[0]

    def __call__(self, value, all_values, output_array):
        if not STRONG_PASS_RE.match(value):
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


def authenticated(handler):
    async def wrapper(request, *args):
        sid = request.cookies.get('sid')
        if sid:
            with await request.app['db'].cursor() as cur:
                await cur.execute("SELECT FROM session uid WHERE sid = %s", [sid])
                if cur.rowcount == 0:
                    return web.Response(body='Not authenticated', status=401)
            return await handler(request, *args)
        else:
            return web.Response(body='Not authenticated', status=401)

    return wrapper


@validate(CREATE_USER_VALIDATOR)
async def create_user(request, valid_data):
    if not valid_data:
        return
    await request.app.db.execute(
        'SELECT EXISTS (SELECT TRUE FROM project."user" WHERE username=%s);',
        [valid_data['username']]
    )
    if request.app.db.fetchone()[0]:
        return web.Response(
            body=json.dumps({'status': 'fail', 'message': 'User with this username already exist'}).encode(),
            status=409
        )
    salt = uuid4().hex
    pass_hash = sha512(valid_data['password'].encode() + salt.encode()).hexdigest()
    await request.app.db.execute('''
            INSERT INTO project.user (username, passhash, salt, email)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', [valid_data['username'], pass_hash, salt, valid_data['email']])
    uid = request.app.db.fetchone()[0]
    return web.Response(body=json.dumps({'status': 'success', 'message': 'User created', 'id': uid}).encode())


@validate(LOGIN_VALIDATOR)
async def login_handler(request, valid_data):
    if not valid_data:
        return
    await request.app.db.execute('SELECT id, passhash, salt FROM project."user" WHERE username = %s',
                                 [valid_data['username']])
    if request.app.db.rowcount == 0:
        return web.Response(body=json.dumps({'status': 'fail', 'message': 'No such user'}).encode(),
                            status=400)
    user_id, pass_hash, salt = request.application.db.fetchone()
    if sha512(valid_data['password'].encode() + salt.encode()).hexdigest() != pass_hash:
        return web.Response(body=json.dumps({'status': 'fail', 'message': 'Incorrect password'}).encode(),
                            status=400)
    response = web.Response(body=json.dumps({'status': 'success', 'message': 'Login successful'}).encode())
    sid = uuid4().hex
    await request.app.db.execute("INSERT INTO session (uid, sid) values (%s, %s)", [user_id, sid])
    response.set_cookie('sid', str(sid))
    return response
