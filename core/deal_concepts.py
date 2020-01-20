# -*- coding: utf-8 -*-
import re
import os
import yaml
import json
from collections import defaultdict
import sys
import xlrd
import logging
logging.basicConfig(level=logging.INFO)

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cpts_with_single_name = set()
cpts_with_multi_name = set()
inverted_index = defaultdict(list)


class ConceptIdxDealer(object):
    def __init__(self, need_update=True):
        self.need_update = need_update
        self.inversed_index = {}
        self.forward_index = {}
        self.concept2idx = {}
        self.cpts_len = 0
        self.concepts_rw_path = module_path + '/data/concepts/'


    def read_one_file(self, book):
        fp = self.concepts_rw_path + 'concept_' + book + '.xlsx'
        data = xlrd.open_workbook(fp)
        table = data.sheets()[0]
        data_list = []
        for i in range(table.nrows):
            data_list.append(table.row_values(i))
        return data_list

    def mark_idx(self, cpts):
        '''
        :param cpts: 同义词组表示的cpts
        :return:
        '''
        old_idx = None
        for cpt in cpts:
            if cpt in self.concept2idx:
                old_idx = self.concept2idx[cpt]
                break
        idx = old_idx if old_idx else self.cpts_len
        for cpt in cpts:
            if not cpt:
                continue
            self.concept2idx[cpt] = idx
        if not old_idx:
            self.cpts_len += 1
        return

    def run(self, books, **params):
        for book in books:
            row = self.read_one_file(book)
            for concepts in row:
                concepts = [concept.lower()
                            for concept in concepts if concept != '']
                self.mark_idx(concepts)
        if self.need_update:
            with open(self.concepts_rw_path + 'all_concepts.csv', 'w+') as f:
                for concept, idx in sorted(self.concept2idx.items(),key=lambda x:x[1]):
                    f.write('{}::{}\n'.format(concept, idx))
        return self.concept2idx


class ConceptCountDealer(object):
    def __init__(self):
        self.concepts_fp = module_path + '/data/concepts/all_concepts.csv'
        self.corpus_path = module_path + '/data/corpus/'
        self.concept2idx = {}

    def count_one(self, book, book_info):
        with open(self.corpus_path + book + '.json', 'r') as f:
            text = json.load(f)
        document_page_range = range(int(book_info['document_st_page']), int(book_info['document_end_page']) + 1)
        import pdb;pdb.set_trace()
        document_text = [text[str(i)] for i in document_page_range]
        
        for concept, idx in self.concept2idx.items():
            result = self.count_one_concept(concept, document_text)
            print('concept: {},page idx: {}'.format(concept, result))
            import pdb;pdb.set_trace()


        

    def count_one_concept(self, concept, document_text):
        res = []

        # '(' ,')'是正则表达式中的元字符，所以要把查询pattern中的'('替换为'\('
        concept = concept.replace('(','\(').replace(')','\)')
        word_pages_fre = [len(re.findall('[\n ]?{}[\n ]?'.format(concept), text)) for text in document_text]
        word_pages = []
        for i, num in enumerate(word_pages_fre):
            res.extend([i+1]*num)

        res.extend(word_pages)
        return res


    def load_concepts(self):
        with open(self.concepts_fp,'r') as f:
            for line in f:
                concept, idx = line.strip().split('::')
                self.concept2idx[concept] = idx
    
    def load_books_info(self, fp_path):
        with open(fp_path, 'r') as f:
            book2book_info = yaml.load(f, Loader=yaml.BaseLoader)
        return book2book_info




    def run(self, books, **params):
        books_info_conf = params.get('conf', {}).get('books_info_conf')
        books_info_conf = module_path + books_info_conf
        self.load_concepts()
        book2book_info = self.load_books_info(books_info_conf)
        for book in books:
            book_info = book2book_info.get(book)
            self.count_one(book, book_info)
            pass





def main():
    books = ['1L2RM', 'StatisticalModels', 'ComputationalStatistics']
    dealer = ConceptIdxDealer()
    concepts = dealer.run(books)
    print(concepts)
    return concepts


if __name__ == '__main__':
    main()
