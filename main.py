# -*- coding: utf-8 -*-
import yaml
import time
import logging
import argparse
logging.basicConfig(level=logging.WARNING)
from textbook_extraction.core.pdf_corpus_extractor import PdfCorpusExtractor
from textbook_extraction.core.deal_concepts import ConceptIdxDealer, ConceptCountDealer, ConceptStatisticDealer
from textbook_extraction.core.books_dealer import LinksDealer

class MainHandler():
    def __init__(self, conf_path, handlers=None):
        with open(conf_path) as f:
            self.conf = yaml.load(f, Loader=yaml.BaseLoader)
        self.handlers = handlers if handlers is not None else []

    def run(self):
        books = self.conf['books']
        logging.warning('deal books: {}'.format(','.join(books)))
        for handler in handlers:
            st = time.time()
            logging.warning('{} begin to deal.'.format(handler.__class__.__name__))
            handler.run(books, conf=self.conf)
            logging.warning('{} finish in {} seconds'.format(handler.__class__.__name__, time.time()-st))

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf_path')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = get_args()
    conf_path = args.conf_path
    handlers = [
        PdfCorpusExtractor(force_create=False),
        ConceptIdxDealer(),
        ConceptCountDealer(),
        ConceptStatisticDealer(),
        LinksDealer()
    ]
    main_handler = MainHandler(conf_path, handlers)
    main_handler.run()
