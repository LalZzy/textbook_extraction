# -*- coding: utf-8 -*-
import yaml
import time
import logging 
logging.basicConfig(level=logging.WARNING)
from textbook_extraction.core.pdf_corpus_extractor import PdfCorpusExtractor
from textbook_extraction.core.deal_concepts import ConceptIdxDealer, ConceptCountDealer


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

if __name__ == '__main__':
    conf_path = 'conf/task_conf.yaml'
    handlers = [
        PdfCorpusExtractor(force_create=False),
        ConceptIdxDealer(),
        ConceptCountDealer()

    ]
    main_handler = MainHandler(conf_path, handlers)
    main_handler.run()
