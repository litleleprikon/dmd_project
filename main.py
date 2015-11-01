#!/usr/bin/env python
import momoko
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from configparser import ConfigParser
from tornado.web import Application
from web_application.auth import UserHandler, LoginHandler

__author__ = 'litleleprikon'


def main():
    config = ConfigParser()
    config.read('config.ini')
    config = config
    handlers = [
        (r"/user", UserHandler),
        (r'/login', LoginHandler)
    ]
    settings = dict(
        app_title=u"InnopolisU publications management system",
        # xsrf_cookies=True,
        cookie_secret=config['WEBSERVICE']['CookieSecret'],
        debug=True,
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
    http_server.listen(8888, 'localhost')
    ioloop.start()


if __name__ == '__main__':
    main()

