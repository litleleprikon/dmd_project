#!/usr/bin/env python
from tornado import gen
from tornado.escape import json_encode
from tornado.web import authenticated
from web_application.auth import AuthReqHandler
from web_application.publications import GetOrderedPublications

__author__ = 'litleleprikon'


class SimpleRelated(AuthReqHandler):
    @authenticated
    @gen.coroutine
    def get(self, pub_id):
        cursor = yield self.application.db.execute('''
        SELECT thesaurus
        FROM project.thesaurus_of_publication
        WHERE publication = %s''', [pub_id])
        thesauruses = [x[0] for x in cursor]
        cursor = yield self.application.db.execute('''
        SELECT publication, count(1) AS c from project.thesaurus_of_publication
        WHERE thesaurus = ANY(%s)
        GROUP BY publication ORDER BY c DESC LIMIT 5
        ''', [thesauruses if len(thesauruses) else None])
        related = [x[0] for x in cursor] if cursor.rowcount > 0 else None

        cursor = yield self.application.db.execute(GetOrderedPublications.generate('publication', related),
                                                   [related])
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


class TfIdfRelated(AuthReqHandler):
    @authenticated
    @gen.coroutine
    def get(self, pub_id):
        cursor = yield self.application.db.execute('''
        SELECT word_id FROM project.tf_idf
        WHERE publication_id = %s
        ORDER BY tf_idf
        DESC LIMIT 10
        ''', [pub_id])
        keywords = [x[0] for x in cursor]
        cursor = yield self.application.db.execute('''
        SELECT publication_id, sum(tf_idf) AS s FROM project.tf_idf
        WHERE word_id = ANY(%s)
        GROUP BY publication_id ORDER BY s LIMIT 5
        ''', [keywords if len(keywords) else None])
        related = [x[0] for x in cursor] if cursor.rowcount > 0 else None

        cursor = yield self.application.db.execute(GetOrderedPublications.generate('publication', related),
                                                   [related])

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
    (r'/api/related/simple/([0-9]+)/?', SimpleRelated),
    (r'/api/related/tfidf/([0-9]+)/?', TfIdfRelated),
]