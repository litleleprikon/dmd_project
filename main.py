#!/usr/bin/env python
import asyncio
from aiohttp import web
from pyDBMS.pyDBMS.connection import connect
from web_application.auth import create_user, login_handler
from web_application.publications import PublicationsListHandler, BooksListHandler, JournalsListHandler, \
    PublicationHandler, BookHandler, ConferenceHandler, JournalHandler
from web_application.ranking import SearchHandler
from web_application.related import SimpleRelated, TfIdfRelated

__author__ = 'litleleprikon'


async def create_connection(loop):
    connection = await connect(loop)
    return await connection.cursor()


app = web.Application()
app.router.add_route('POST', '/api/user', create_user)
app.router.add_route('POST', '/api/login', login_handler)
app.router.add_route('GET', r'/api/publications', PublicationsListHandler().get)
app.router.add_route('GET', r'/api/books', BooksListHandler().get)
app.router.add_route('GET', r'/api/conferences', JournalsListHandler().get)
app.router.add_route('GET', r'/api/journals', JournalsListHandler().get)
app.router.add_route('GET', r"/api/publications/{pub_id:\d+}", PublicationHandler().get)
app.router.add_route('GET', r"/api/books/{pub_id:\d+}", BookHandler().get)
app.router.add_route('GET', r"/api/conferences/{pub_id:\d+}", ConferenceHandler().get)
app.router.add_route('GET', r"/api/journals/{pub_id:\d+}", JournalHandler().get)
app.router.add_route('GET', r'/api/search', SearchHandler().get)
app.router.add_route('GET', r'/api/related/simple/{pub_id:\d+}', SimpleRelated().get)
app.router.add_route('GET', r'/api/related/tfidf/{pub_id:\d+}', TfIdfRelated().get)


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

