#!/usr/bin/env python
from tornado import gen
from tornado.escape import json_encode
from tornado.web import authenticated, asynchronous
from web_application.auth import AuthReqHandler

__author__ = 'litleleprikon'


MINIMUM_PAGE_SIZE = 4


class GetOrderedPublications:
    GET_SQL = '''
        SELECT p.id, p.title, p.abstract, pt.name AS p_type from project.{main_table:s} AS p
        LEFT JOIN project.publication_type as pt ON p.type = pt.id
        {join:s}
        WHERE p.id = ANY(%s)
        {order:s}
    '''

    JOIN_SQL = '''
    LEFT JOIN (VALUES {values:s}) as x(id, ordering) ON p.id = x.id
    '''

    @classmethod
    def generate_join(cls, values):
        if values is not None:
            values_str = ', '.join(map(lambda x: '({}, {})'.format(str(x[0]), str(x[1])), enumerate(values)))
            return cls.JOIN_SQL.format(values=values_str)
        return ''

    @classmethod
    def generate(cls, table, values):
        join = cls.generate_join(values)
        order = ' ORDER BY x.ordering ' if len(join) else ''
        return cls.GET_SQL.format(main_table=table, join=join, order=order)


class PublicationsListHandler(AuthReqHandler):
    GET_SQL = '''
    SELECT p.id, p.title, p.abstract, pt.name AS p_type from project.publication AS p
    LEFT JOIN project.publication_type as pt ON p.type = pt.id
    ORDER BY p.{0:s}
    LIMIT %(limit)s
    OFFSET %(offset)s
'''

    @authenticated
    @gen.coroutine
    def get(self):
        arguments = self.request.arguments
        page = 0 if arguments.get('page') is None else int(arguments['page'][0])
        page_size = MINIMUM_PAGE_SIZE if arguments.get('psize') is None else int(arguments['psize'][0])
        sort_column = 0 if arguments.get('sort') is None else int(arguments['sort'][0])
        if sort_column > 1:
            sort_column = 1
        ordering = ['title', 'year DESC']
        sql = self.GET_SQL.format(ordering[sort_column])
        cursor = yield self.application.db.execute(sql, {'limit': page_size, 'offset': page*page_size})
        result = []  # TODO create index on title and year
        for publication in cursor:
            temp = {
                'id': publication[0],
                'title': publication[1],
                'abstract': publication[2],
                'p_type': publication[3]
            }
            result.append(temp)
        self.finish(json_encode(result))


class BooksListHandler(PublicationsListHandler):
    GET_SQL = '''
    SELECT p.id, p.title, p.abstract, pt.name AS p_type from project.book AS p
    LEFT JOIN project.publication_type as pt ON p.type = pt.id
    ORDER BY p.{0:s}
    LIMIT %(limit)s
    OFFSET %(offset)s
'''


class ConferencesListHandler(PublicationsListHandler):
    GET_SQL = '''
    SELECT p.id, p.title, p.abstract, pt.name as p_type from project.conference AS p
    LEFT JOIN project.publication_type as pt ON p.type = pt.id
    ORDER BY p.{0:s}
    LIMIT %(limit)s
    OFFSET %(offset)s
    '''


class JournalsListHandler(PublicationsListHandler):
    GET_SQL = '''
    SELECT p.id, p.title, p.abstract, pt.name AS p_type from project.journal AS p
    LEFT JOIN project.publication_type as pt ON p.type = pt.id
    ORDER BY p.{0:s}
    LIMIT %(limit)s
    OFFSET %(offset)s
    '''


class PublicationHandler(AuthReqHandler):
    SQL_GET = '''
    SELECT p.id as id,
    title,
    year,
    pr.name as publisher,
    pdf,
    pt.name as type,
    abstract,
    ar_number,
    doi,
    end_page,
    md_url,
    part_num,
    start_page  FROM project.publication AS p
    LEFT JOIN project.publisher AS pr ON p.publisher = pr.id
    LEFT JOIN project.publication_type AS pt ON p.type = pt.id WHERE p.id = %s
    '''

    @gen.coroutine
    def add_authors(self, record):
        d_id = record['id']
        authors = []
        cursor = yield self.application.db.execute('''
        SELECT a.name
        FROM project.author_of_publication AS ap
        LEFT JOIN project.author AS a ON a.id = ap.author_id
        WHERE ap.publication_id = %s
        ''', [d_id])
        for author in cursor:
            authors.append(author[0])
        record['authors'] = authors

    @gen.coroutine
    def add_collections(self, record):
        pass

    @authenticated
    @gen.coroutine
    def get(self, pub_id):
        cursor = yield self.application.db.execute(self.SQL_GET, [pub_id])
        if cursor.rowcount == 0:
            self.set_status(404)
            self.finish(json_encode({'status': 'fail', 'message': 'Publication not found'}))
            return
        data = cursor.fetchone()
        record = {x.name: data[i] for i, x in enumerate(cursor.description)}
        yield self.add_authors(record)
        yield self.add_collections(record)
        self.write(json_encode(record))
        self.finish()


class BookHandler(PublicationHandler):
    SQL_GET = '''
    SELECT p.id as id,
    title,
    year,
    pr.name as publisher,
    pdf,
    pt.name as type,
    abstract,
    ar_number,
    doi,
    end_page,
    md_url,
    part_num,
    start_page,
    isbn,
    pub_title
    FROM project.book AS p
    LEFT JOIN project.publisher AS pr ON p.publisher = pr.id
    LEFT JOIN project.publication_type AS pt ON p.type = pt.id WHERE p.id = %s
    '''


class ConferenceHandler(PublicationHandler):
    SQL_GET = '''
    SELECT p.id as id,
    title,
    year,
    pr.name as publisher,
    pdf,
    pt.name as type,
    abstract,
    ar_number,
    doi,
    end_page,
    md_url,
    part_num,
    start_page,
    affiliation,
    isbn,
    pu_number
    FROM project.conference AS p
    LEFT JOIN project.publisher AS pr ON p.publisher = pr.id
    LEFT JOIN project.publication_type AS pt ON p.type = pt.id WHERE p.id = %s
    '''

    @gen.coroutine
    def add_collections(self, record):
        d_id = record['id']
        thesauruses = []
        cursor = yield self.application.db.execute('''
        SELECT t.word
        FROM project.thesaurus_of_publication as tp
        LEFT JOIN project.thesaurus as t ON tp.thesaurus = t.id
        WHERE tp.publication = %s;
        ''', [d_id])
        for thesaurus in cursor:
            thesauruses.append(thesaurus[0])
        record['thesauruses'] = thesauruses


class JournalHandler(PublicationHandler):
    SQL_GET = '''
    SELECT p.id as id,
    title,
    year,
    pr.name as publisher,
    pdf,
    pt.name as type,
    abstract,
    ar_number,
    doi,
    end_page,
    md_url,
    part_num,
    start_page,
    affiliations,
    issn,
    issue,
    pub_title,
    pu_number,
    volume
    FROM project.journal AS p
    LEFT JOIN project.publisher AS pr ON p.publisher = pr.id
    LEFT JOIN project.publication_type AS pt ON p.type = pt.id WHERE p.id = %s
    '''

    @gen.coroutine
    def add_collections(self, record):
        d_id = record['id']
        thesauruses = []
        cursor = yield self.application.db.execute('''
        SELECT t.word
        FROM project.thesaurus_of_publication as tp
        LEFT JOIN project.thesaurus as t ON tp.thesaurus = t.id
        WHERE tp.publication = %s;
        ''', [d_id])
        for thesaurus in cursor:
            thesauruses.append(thesaurus[0])
        record['thesauruses'] = thesauruses

HANDLERS = [
    (r'/api/publications/?', PublicationsListHandler),
    (r'/api/books/?', BooksListHandler),
    (r'/api/conferences/?', JournalsListHandler),
    (r'/api/journals/?', JournalsListHandler),
    (r"/api/publications/([0-9]+)/?", PublicationHandler),
    (r"/api/books/([0-9]+)/?", BookHandler),
    (r"/api/conferences/([0-9]+)/?", ConferenceHandler),
    (r"/api/journals/([0-9]+)/?", JournalHandler)
]