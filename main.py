#!/usr/bin/env python
# from tornado import gen
# from tornado.platform.asyncio import AsyncIOMainLoop
import asyncio
# from tornado.httpserver import HTTPServer
from configparser import ConfigParser
# from tornado.web import Application
from aiohttp import web

from pyDBMS.pyDBMS.connection import connect
# from web_application.auth import HANDLERS as auth_handlers, create_user, login_handler
# from web_application.publications import HANDLERS as pub_handlers
# from web_application.related import HANDLERS as related_handlers
# from web_application.ranking import HANDLERS as ranking_handlers
from web_application.auth import create_user, login_handler

__author__ = 'litleleprikon'


async def create_connection(loop):
    connection = await connect(loop)
    return await connection.cursor()


app = web.Application()
app.router.add_route('POST', '/api/user', create_user)
app.router.add_route('POST', '/api/login', login_handler)

loop = asyncio.get_event_loop()
app.db = loop.run_until_complete(create_connection(loop))
handler = app.make_handler()
f = loop.create_server(handler, 'localhost', 8080)
srv = loop.run_until_complete(f)
print('serving on', srv.sockets[0].getsockname())
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.run_until_complete(handler.finish_connections(1.0))
    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.run_until_complete(app.finish())
loop.close()

