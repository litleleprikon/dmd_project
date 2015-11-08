#!/usr/bin/env python
import momoko
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from configparser import ConfigParser
from tornado.web import Application
from web_application.auth import HANDLERS as auth_handlers
from web_application.publications import HANDLERS as pub_handlers
from web_application.related import HANDLERS as related_handlers
from web_application.ranking import HANDLERS as ranking_handlers

__author__ = 'litleleprikon'


def main():
    config = ConfigParser()
    config.read('config.ini')
    config = config

    handlers = []
    handlers.extend(pub_handlers)
    handlers.extend(auth_handlers)
    handlers.extend(related_handlers)
    handlers.extend(ranking_handlers)

    settings = dict(
        app_title=u"InnopolisU publications management system",
        # xsrf_cookies=True,
        cookie_secret=config['WEBSERVICE']['CookieSecret'],
        debug=True,
        login_url='/api/login'
    )
    application = Application(handlers=handlers, **settings)
    ioloop = IOLoop.instance()
    application.db = momoko.Pool(
        dsn='dbname={database:s} user={user:s} password={password:s} host={host:s} port=5432'.format(**config['DATABASE']),
        size=2,
        ioloop=ioloop,
    )

    future = application.db.connect()
    ioloop.add_future(future, lambda f: ioloop.stop())
    ioloop.start()
    future.result()  # raises exception on connection error

    http_server = HTTPServer(application)
    http_server.listen(8080, '0.0.0.0')
    ioloop.start()


if __name__ == '__main__':
    main()

