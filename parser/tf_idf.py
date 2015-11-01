#!/usr/bin/env python
from configparser import ConfigParser
import re
from psycopg2 import connect

__author__ = 'litleleprikon'

SPLIT_RE = re.compile(r" |(?<! |[',\\.:!()@/<>])(?=[',\\.:!()@/<>])|(?<=[',\\.:!()@/<>])(?![',\\.:!()@/<>])",
                      re.IGNORECASE)
REMOVE_TAGS_RE = re.compile(r'<[A-Za-z\/][^>]*>')


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
    cursor.execute('SELECT abstract from project.publication limit 10')
    for abstract in cursor:
        for word in SPLIT_RE.split(abstract[0]):
            word = REMOVE_TAGS_RE.sub('', word).lower()
            cursor2.execute('select id from project.temp_word where word = %s', [word])
            if cursor2.rowcount == 0:
                cursor2.execute('insert into project.temp_word (word) VALUES (%s) returning id', [word])
            w_id = cursor2.fetchone()[0]
            cursor2.execute('UPDATE project.temp_word SET count = count + 1 WHERE id = %s', [w_id])


def main():
    count_words()


if __name__ == '__main__':
    main()