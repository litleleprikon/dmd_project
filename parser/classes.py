#!/usr/bin/env python
from psycopg2 import connect
from configparser import ConfigParser

__author__ = 'litleleprikon'


def get_collection(obj):
    return '' if obj is None else [get_text(i) for i in obj.iter()]


def mk_int(s):
    s = ''.join(filter(str.isdigit, s))
    s = s.strip()
    return int(s) if s else 0


def get_text(obj):
    return '' if obj is None else ' '.join(obj.itertext())


class DBConnection:
    _instance = None
    _connection = None

    def get_config(self):
        return ConfigParser().read('../config.ini')['DATABASE']

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            config = self.get_config()
            self._connection = connect(database=config['Database'], user=config['User'], password=config['Password'],
                                       host=config['Host'])
            self._connection.autocommit = True
            self.cursor = self._connection.cursor()
            self.cursor.execute("SET SCHEMA 'project'")

    def __del__(self):
        if self._connection is not None:
            self._connection.close()


class Author:
    _instances = dict()

    def __new__(cls, name):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]

    def __init__(self, name):
        self.name = name
        self._id = self.__select(name)
        if self._id is None:
            self._id = self.__create()

    def __len__(self):
        return len(self._instances)

    def __select(self, name):
        DBConnection().cursor.execute('SELECT id FROM author WHERE name = %s', [name])
        res = DBConnection().cursor.fetchone()[0]
        return res if res is None else res[0]

    def __create(self):
        DBConnection().cursor.execute('INSERT INTO author (name) VALUES (%s) RETURNING id', [self.name])
        return DBConnection().cursor.fetchone()[0]

    def link_with_publication(self, pub_id):
        DBConnection().cursor.execute('INSERT INTO author_of_publication (author_id, publication_id) VALUES (%s, %s)',
                                      [self._id, pub_id])


class Publisher:
    _instances = dict()

    def __new__(cls, name):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]

    def __init__(self, name):
        if hasattr(self, '_id'):
            return
        self.name = name
        self._id = self.__select(name)
        if self._id is None:
            self._id = self.__save()

    def __select(self, name):
        DBConnection().cursor.execute('SELECT id FROM project.publisher WHERE name = %s', [name])
        res = DBConnection().cursor.fetchone()
        return res if res is None else res[0]

    def __save(self):
        DBConnection().cursor.execute('INSERT INTO publisher (name) VALUES (%s) RETURNING id', [self.name])
        return DBConnection().cursor.fetchone()[0]

    def __int__(self):
        return self._id


class PubType:
    _instances = dict()

    def __new__(cls, name, *args, **kwargs):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]

    def __init__(self, name):
        if hasattr(self, '_id'):
            return
        self.name = name
        self._id = self.__select(name)
        if self._id is None:
            self._id = self.__save()

    def __select(self, name):
        DBConnection().cursor.execute('SELECT id FROM project.publication_type WHERE name = %s', [name])
        res = DBConnection().cursor.fetchone()
        return res if res is None else res[0]

    def __save(self):
        DBConnection().cursor.execute('INSERT INTO publication_type (name) VALUES (%s) RETURNING id', [self.name])
        return DBConnection().cursor.fetchone()[0]

    def __int__(self):
        return self._id


class Thesaurus:
    def __init__(self, word):
        self.word = word
        self._id = self.__select(word)
        if self._id is None:
            self._id = self.__create()

    def __select(self, word):
        DBConnection().cursor.execute('SELECT id FROM thesaurus WHERE word = %s', [word])
        res = DBConnection().cursor.fetchone()
        return res if res is None else res[0]

    def __create(self):
        DBConnection().cursor.execute('INSERT INTO thesaurus (word) VALUES (%s) RETURNING id', [self.word])
        return DBConnection().cursor.fetchone()[0]

    def link_with_publication(self, pub_id):
        DBConnection().cursor.execute('INSERT INTO thesaurus_of_publication (thesaurus, publication) VALUES (%s, %s)',
                                      [self._id, pub_id])


class Publication:
    def __init__(self, document_object):
        self.id = None
        self.title = get_text(document_object.find('title'))
        self.year = mk_int(get_text(document_object.find('py')))
        self.authors = map(Author, get_text(document_object.find('authors')).split(';'))
        self._publisher = Publisher(get_text(document_object.find('publisher')))
        self.pdf = get_text(document_object.find('pdf'))
        self._type = PubType(get_text(document_object.find('pubtype')))
        self.abstract = get_text(document_object.find('abstract'))
        self.ar_number = mk_int(get_text(document_object.find('arnumber')))
        self.doi = get_text(document_object.find('doi'))
        self.start_page = mk_int(get_text(document_object.find('spage')))
        self.end_page = mk_int(get_text(document_object.find('epage')))
        self.md_url = get_text(document_object.find('mdurl'))
        self.part_num = mk_int(get_text(document_object.find('partnum')))

    @property
    def publisher(self):
        return int(self._publisher)

    @property
    def type(self):
        return int(self._type)

    def __getitem__(self, item):
        return getattr(self, item)

    def push(self):
        raise NotImplementedError()


class Book(Publication):
    def __init__(self, document_object):
        super().__init__(document_object)
        self.isbn = get_text(document_object.find('isbn')).replace('-', '')
        self.pub_title = get_text(document_object.find('pubtitle'))

    def push(self):
        sql = """
INSERT INTO project.book (
    title,
    year,
    publisher,
    pdf,
    type,
    abstract,
    ar_number,
    doi,
    end_page,
    md_url,
    part_num,
    start_page,
    isbn,
    pub_title
)
VALUES (
  %(title)s,
  %(year)s,
  %(publisher)s,
  %(pdf)s,
  %(type)s,
  %(abstract)s,
  %(ar_number)s,
  %(doi)s,
  %(end_page)s,
  %(md_url)s,
  %(part_num)s,
  %(start_page)s,
  %(isbn)s,
  %(pub_title)s
)
RETURNING id
        """
        DBConnection().cursor.execute(sql, self)
        self.id = DBConnection().cursor.fetchone()[0]
        map(lambda x: x.link_with_publication(self.id), self.authors)


class Conference(Publication):
    def __init__(self, document_object):
        super().__init__(document_object)
        self.affiliation = get_text(document_object.find('affiliation'))
        self.thesaurus = map(Thesaurus, get_collection(document_object.find('thesaurusterms')))
        self.isbn = get_text(document_object.find('isbn')).replace('-', '')
        self.pu_number = mk_int(get_text(document_object.find('punumber')))

    def push(self):
        sql = """
INSERT INTO project.conference (
    title,
    year,
    publisher,
    pdf,
    type,
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
)
VALUES (
  %(title)s,
  %(year)s,
  %(publisher)s,
  %(pdf)s,
  %(type)s,
  %(abstract)s,
  %(ar_number)s,
  %(doi)s,
  %(end_page)s,
  %(md_url)s,
  %(part_num)s,
  %(start_page)s,
  %(affiliation)s,
  %(isbn)s,
  %(pu_number)s
)
RETURNING id
        """
        DBConnection().cursor.execute(sql, self)
        self.id = DBConnection().cursor.fetchone()[0]
        map(lambda x: x.link_with_publication(self.id), self.authors)
        map(lambda x: x.link_with_publication(self.id), self.thesaurus)


class Journal(Publication):
    def __init__(self, document_object):
        super().__init__(document_object)
        self.affiliations = get_text(document_object.find('affiliation'))
        self.thesaurus = map(Thesaurus, get_collection(document_object.find('thesaurusterms')))
        self.pu_number = mk_int(get_text(document_object.find('punumber')))
        self.pub_title = get_text(document_object.find('pubtitle'))
        self.issn = get_text(document_object.find('issn')).replace('-', '')
        self.issue = get_text(document_object.find('issue'))
        self.volume = mk_int(get_text(document_object.find('volume')))

    def push(self):
        sql = """
INSERT INTO project.journal (
    title,
    year,
    publisher,
    pdf,
    type,
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
)
VALUES (
  %(title)s,
  %(year)s,
  %(publisher)s,
  %(pdf)s,
  %(type)s,
  %(abstract)s,
  %(ar_number)s,
  %(doi)s,
  %(end_page)s,
  %(md_url)s,
  %(part_num)s,
  %(start_page)s,
  %(affiliations)s,
  %(issn)s,
  %(issue)s,
  %(pub_title)s,
  %(pu_number)s,
  %(volume)s
)
RETURNING id
        """
        DBConnection().cursor.execute(sql, self)
        self.id = DBConnection().cursor.fetchone()[0]
        map(lambda x: x.link_with_publication(self.id), self.authors)
        map(lambda x: x.link_with_publication(self.id), self.thesaurus)


class Singleton(object):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls._instances.get(cls, None) is None:
            cls._instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)

        return Singleton._instances[cls]


class Test(Singleton):
    def __init__(self):
        print('init')


def main():
    # a = [Author('asd'), Author('asd'), Author('wer'), Author('asd')]
    # print(len(a[0]))
    # DBConnection().execute('SELECT 1')
    Test()
    Test()
    Test()
    Test()


if __name__ == '__main__':
    main()
