#!/usr/bin/env python
import re
from tornado import gen
from tornado.escape import json_encode
from tornado.ioloop import IOLoop
from web_application.auth import AuthReqHandler
from web_application.base import DBConnection
from web_application.publications import GetOrderedPublications

__author__ = 'litleleprikon'

SPLIT_RE = re.compile(r" |(?<! |[',\\.:!()@/<>])(?=[',\\.:!()@/<>])|(?<=[',\\.:!()@/<>])(?![',\\.:!()@/<>])",
                      re.IGNORECASE)

MINIMUM_PAGE_SIZE = 10


class SearchHandler(AuthReqHandler):
    @gen.coroutine
    def get(self):
        arguments = self.request.arguments
        page = 0 if arguments.get('page') is None else int(arguments['page'][0])
        page_size = MINIMUM_PAGE_SIZE if arguments.get('psize') is None else int(arguments['psize'][0])
        search_query = arguments['q'][0] if arguments.get('q') is not None else ''
        search_query = search_query.decode().lower()
        words = SPLIT_RE.split(search_query)
        words = None if len(words) == 0 else words
        cursor = yield self.application.db.execute('''
            SELECT id FROM project.keyword WHERE word = ANY(%s)
            ''', [words])
        words_id = [x[0] for x in cursor] if cursor.rowcount > 0 else None
        cursor = yield self.application.db.execute('''
            SELECT publication_id, sum(tf_idf) AS s FROM project.tf_idf
            WHERE word_id = ANY(%s)
            GROUP BY publication_id ORDER BY s LIMIT %s OFFSET %s
            ''', [words_id, page_size, page*page_size])
        publications_id = [x[0] for x in cursor] if cursor.rowcount > 0 else None
        cursor = yield self.application.db.execute(GetOrderedPublications.generate('publication', publications_id),
                                                   [publications_id])
        result = []
        for publication in cursor:
            temp = {
                'id': publication[0],
                'title': publication[1],
                'abstract': publication[2],
                'p_type': publication[3]
            }
            result.append(temp)
        self.finish(json_encode(result))

HANDLERS = [
    (r'/api/search', SearchHandler)
]