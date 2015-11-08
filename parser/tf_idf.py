#!/usr/bin/env python
from configparser import ConfigParser
import re
from psycopg2 import connect
from datetime import datetime

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
# con.autocommit = True

cursor = con.cursor()
cursor2 = con.cursor()


def count_words():
    page = 0
    while True:
        start = datetime.now()
        cursor.execute('SELECT id, abstract from project.publication LIMIT 100 OFFSET %s', [page*100])
        page += 1
        if cursor.rowcount == 0:
            break

        for abstract in cursor:
            d_id = abstract[0]
            abstract = REMOVE_TAGS_RE.sub('', abstract[1]).lower()
            words = [x for x in SPLIT_RE.split(abstract) if x not in stop_words]
            word_counts = dict()
            for word in words:
                if word in word_counts:
                    word_counts[word] += 1
                else:
                    word_counts[word] = 1
            cursor2.execute('select word, id from project.keyword where word = ANY(%s)', [list(word_counts.keys())])
            words_ids = {x[0]: x[1] for x in cursor2}
            missed_words = [x for x in words if x not in words_ids]

            values = ', '.join(["('{}')".format(x.replace("'", "''")) for x in missed_words])

            if missed_words:
                query = 'insert into project.keyword (word) VALUES {} RETURNING word, id'.format(values)
                cursor2.execute(query)

                for x in cursor2:
                    words_ids[x[0]] = x[1]

            for_insert = [{
                'word_id': words_ids[word],
                'count': word_counts[word],
                'publication_id': d_id
            } for word in words_ids]

            cursor2.executemany('''
            INSERT INTO project.word_in_text (word_id, publication_id, count)
            VALUES (%(word_id)s, %(publication_id)s, %(count)s)
            ''', for_insert)
            con.commit()
        print(datetime.now() - start)


def main():
    count_words()


if __name__ == '__main__':
    main()