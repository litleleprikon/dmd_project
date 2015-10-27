#! /usr/bin/env python
from xml.etree import ElementTree as etree
import requests
from parser.classes import *
import logging


__author__ = 'litleleprikon'

API_LINK = 'http://ieeexplore.ieee.org/gateway/ipsSearch.jsp'
DOCS_PER_PAGE = 10
START_YEAR = 2015

logging.basicConfig(filename='errors.log', filemode='w')


DOC_TYPES = {
    'Conferences': Conference,
    'Journals': Journal,
    'Books': Book
}


def log(doc, ex):
    logging.error('''=== On document ===
===================
{0:s}
===================

=== Traceback ===
{0:s}
================='''.format(doc, ex))


def make_request(year, page, ctype):
    response = requests.get(API_LINK, {
        'py': str(year),
        'hc': str(DOCS_PER_PAGE),
        'rs': str(page * DOCS_PER_PAGE + 1),
        'ctype': ctype
    })
    return etree.XML(response.text)


def handle_data_set(parsed_data, doc_type):
    i = 0
    for document in parsed_data.findall('document'):
        try:
            doc_type(document).push()
            i += 1
        except Exception as ex:
            log(document, str(ex))
    return i


def handle_year(year):
    page_number = 0
    counter = 0
    for k in DOC_TYPES.keys():
        parsed_data = make_request(year, page_number, k)
        docs_limit = mk_int(get_text(parsed_data.find('totalfound')))
        counter += handle_data_set(parsed_data, DOC_TYPES[k])
        while counter <= docs_limit:
            parsed_data = make_request(year, page_number, k)
            counter += handle_data_set(parsed_data, DOC_TYPES[k])
            page_number += 1
        return counter


def main_loop():
    counter = 0
    year = START_YEAR
    while counter < 1000000:
        counter += handle_year(year)
        year -= 1


def main():
    main_loop()
    # params = {
    #     'py': '2010',
    #     'hc': '100',
    #     'rs': '2'
    # }
    # response = requests.get(API_LINK, params)
    # parsed_data = etree.XML(response.text)
    # print(list(parsed_data.find('totalfound').itertext())[0])
    # print(response.text)

if __name__ == '__main__':
    main()
