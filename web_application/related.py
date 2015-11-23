#!/usr/bin/env python
import json

from aiohttp import web

from web_application.auth import authenticated
from web_application.publications import GetOrderedPublications

__author__ = 'litleleprikon'


class SimpleRelated:
    @authenticated
    async def get(self, request):
        pub_id = request.match_info['pub_id']
        await request.app.db.execute('''
        SELECT thesaurus
        FROM project.thesaurus_of_publication
        WHERE publication = %s''', [pub_id])
        thesauruses = [x[0] for x in request.app.db]
        await request.app.db.execute('''
        SELECT publication, count(1) AS c from project.thesaurus_of_publication
        WHERE thesaurus = ANY(%s)
        GROUP BY publication ORDER BY c DESC LIMIT 5
        ''', [thesauruses if len(thesauruses) else None])
        related = [x[0] for x in request.app.db] if request.app.db.rowcount > 0 else None

        await request.app.db.execute(GetOrderedPublications.generate('publication', related),
                                                   [related])
        result = []
        for publication in request.app.db:
            temp = {
                'id': publication[0],
                'title': publication[1],
                'abstract': publication[2],
                'p_type': publication[3]
            }
            result.append(temp)
        return web.Response(body=json.dumps(result).encode())


class TfIdfRelated:
    @authenticated
    async def get(self, request):
        pub_id = request.match_info['pub_id']
        await request.app.db.execute('''
        SELECT word_id FROM project.tf_idf
        WHERE publication_id = %s
        ORDER BY tf_idf
        DESC LIMIT 10
        ''', [pub_id])
        keywords = [x[0] for x in request.app.db]
        await request.app.db.execute('''
        SELECT publication_id, sum(tf_idf) AS s FROM project.tf_idf
        WHERE word_id = ANY(%s)
        GROUP BY publication_id ORDER BY s LIMIT 5
        ''', [keywords if len(keywords) else None])
        related = [x[0] for x in request.app.db] if request.app.db.rowcount > 0 else None

        await request.app.db.execute(GetOrderedPublications.generate('publication', related),
                                                   [related])

        result = []
        for publication in request.app.db:
            temp = {
                'id': publication[0],
                'title': publication[1],
                'abstract': publication[2],
                'p_type': publication[3]
            }
            result.append(temp)
        return web.Response(body=json.dumps(result).encode())


HANDLERS = [
    (r'/api/related/simple/([0-9]+)/?', SimpleRelated),
    (r'/api/related/tfidf/([0-9]+)/?', TfIdfRelated),
]