#!/usr/bin/env python
import json
import re

from aiohttp import web

from web_application.auth import authenticated
from web_application.publications import GetOrderedPublications

__author__ = 'litleleprikon'

SPLIT_RE = re.compile(r" |(?<! |[',\\.:!()@/<>])(?=[',\\.:!()@/<>])|(?<=[',\\.:!()@/<>])(?![',\\.:!()@/<>])",
                      re.IGNORECASE)

MINIMUM_PAGE_SIZE = 10


class SearchHandler:
    @authenticated
    async def get(self, request):
        arguments = request.GET
        page = 0 if arguments.get('page') is None else int(arguments['page'][0])
        page_size = MINIMUM_PAGE_SIZE if arguments.get('psize') is None else int(arguments['psize'][0])
        search_query = arguments['q'][0] if arguments.get('q') is not None else ''
        search_query = search_query.decode().lower()
        words = SPLIT_RE.split(search_query)
        words = None if len(words) == 0 else words
        await request.app.db.execute('''
            SELECT id FROM project.keyword WHERE word = ANY(%s)
            ''', [words])
        words_id = [x[0] for x in request.app.db] if request.app.db.rowcount > 0 else None
        await request.app.db.execute('''
            SELECT publication_id, sum(tf_idf) AS s FROM project.tf_idf
            WHERE word_id = ANY(%s)
            GROUP BY publication_id ORDER BY s LIMIT %s OFFSET %s
            ''', [words_id, page_size, page*page_size])
        publications_id = [x[0] for x in request.app.db] if request.app.db.rowcount > 0 else None
        await request.app.db.execute(GetOrderedPublications.generate('publication', publications_id),
                                                   [publications_id])
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
