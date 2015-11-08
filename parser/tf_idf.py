#!/usr/bin/env python
from configparser import ConfigParser
import re
from psycopg2 import connect

__author__ = 'litleleprikon'

SPLIT_RE = re.compile(r" |(?<! |[',\\.:!()@/<>])(?=[',\\.:!()@/<>])|(?<=[',\\.:!()@/<>])(?![',\\.:!()@/<>])",
                      re.IGNORECASE)
REMOVE_TAGS_RE = re.compile(r'<[A-Za-z\/][^>]*>')


stop_words = None
with open('stop_words.txt', 'r') as sw:
    stop_words = set(map(lambda x: x.replace('\n', ''), sw.readlines()))


def get_config():
    config = ConfigParser()
    config.read('../config.ini')
    return config['DATABASE']

config = get_config()
con = connect(database=config['Database'], user=config['User'], password=config['Password'],
              host=config['Host'])
con.autocommit = True

cursor = con.cursor()
cursor2 = con.cursor()


def count_words():
    page = 0
    while True:
        cursor.execute('SELECT id, abstract from project.publication LIMIT 10 OFFSET %s', [page*10])
        page += 1
        if cursor.rowcount == 0:
            break

        for abstract in cursor:
            d_id = abstract[0]
            for word in SPLIT_RE.split(abstract[1]):
                word = REMOVE_TAGS_RE.sub('', word).lower()
                if word in stop_words:
                    continue
                cursor2.execute('select id from project.keyword where word = %s', [word])
                if cursor2.rowcount == 0:
                    cursor2.execute('insert into project.keyword (word) VALUES (%s) returning id', [word])
                w_id = cursor2.fetchone()[0]
                cursor2.execute('select id from project.word_in_text where word_id = %s and publication_id = %s',
                                [w_id, d_id])
                if cursor2.rowcount == 0:
                    cursor2.execute('''insert into project.word_in_text (publication_id, word_id) VALUES (%s, %s)''',
                                    [d_id, w_id])
                cursor2.execute('UPDATE project.word_in_text SET count = count + 1 WHERE publication_id = %s and word_id = %s', [d_id, w_id])


def main():
    count_words()


if __name__ == '__main__':
    main()