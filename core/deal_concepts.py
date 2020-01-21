# -*- coding: utf-8 -*-
import re
import os
import yaml
import json
from collections import defaultdict, Counter
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
                for concept, idx in sorted(self.concept2idx.items(), key=lambda x: x[1]):
                    f.write('{}::{}\n'.format(concept, idx))
        return self.concept2idx


class ConceptCountDealer(object):
    def __init__(self):
        self.concepts_fp = module_path + '/data/concepts/all_concepts.csv'
        self.corpus_path = module_path + '/data/corpus/'
        self.concept2idx = {}
        self.book_chapter2idx = {}

    def count_one(self, book, book_info):
        
        with open(self.corpus_path + book + '.json', 'r') as f:
            text = json.load(f)
        document_page_range = range(int(book_info['document_st_page']), int(
            book_info['document_end_page']) + 1)
        document_text = [text[str(i)] for i in document_page_range]

        page_result = dict()
        for concept, idx in self.concept2idx.items():
            page2frequency = self.count_one_concept(concept, document_text)
            print('concept: {},page idx: {}'.format(concept, page2frequency))
            page_result.setdefault(idx, defaultdict(int))
            for page, frequency in page2frequency.items():
                page_result[idx][page] += frequency

        chapter_pages = [int(i) for i in book_info.get('chapter_pages')]
        chapter_result = dict()
        for concept_idx, page_info in page_result.items():
            chater_info = defaultdict(int)
            for page, frequency in page_info.items():
                # import pdb;pdb.set_trace()
                for i in range(len(chapter_pages)-1):
                    if page in range(chapter_pages[i], chapter_pages[i+1]):
                        break
                chapter_idx = self.book_chapter2idx.get(book).get(i)
                chater_info[chapter_idx] += frequency
            chapter_result[concept_idx] = chater_info
        
        result = {'page_result': page_result, 'chapter_result': chapter_result}
        return result


    def save_data(self, book2result, book2book_info):
        for book, result in book2result.items():
            page_result = result['page_result']
            with open(module_path + '/data/concept_page_nums/all_words_info_{}.csv'.format(book), 'w+') as f:
                for concept, page2frequency in page_result.items():
                    for page, frequency in page2frequency.items():
                        f.write('{},{},{},{}\n'.format(book, concept, page, frequency))
        
        with open(module_path + '/data/concept_page_nums/all_words_info.csv', 'w+') as f:
            for book, result in book2result.items():
                chapter_result = result['chapter_result']
                for concept, chp2frequency in chapter_result.items():
                    for chp, frequency in chp2frequency.items():
                        f.write('{},{},{}\n'.format(concept, chp, frequency))

    def count_one_concept(self, concept, document_text):
        record = []

        # '(' ,')'是正则表达式中的元字符，所以要把查询pattern中的'('替换为'\('
        concept = concept.replace('(', '\(').replace(')', '\)')
        word_pages_fre = [len(re.findall('[\n ]?{}[\n ]?'.format(
            concept), text)) for text in document_text]
        word_pages = []
        for i, num in enumerate(word_pages_fre):
            record.extend([i+1]*num)

        record.extend(word_pages)
        frequency = Counter(record)
        return frequency

    def load_concepts(self):
        with open(self.concepts_fp, 'r') as f:
            for line in f:
                concept, idx = line.strip().split('::')
                self.concept2idx[concept] = int(idx)
    
    def mark_chapter_idx(self, books, books_info_conf):
        idx = 0
        for book in books:
            mark = dict()
            chapter_info = books_info_conf.get(book).get('chapter_pages')
            for i, page_num in enumerate(chapter_info[:-1]):
                mark[i] = idx
                idx += 1
            self.book_chapter2idx[book] = mark



    def load_books_info(self, fp_path):
        with open(fp_path, 'r') as f:
            book2book_info = yaml.load(f, Loader=yaml.BaseLoader)
        return book2book_info

    def run(self, books, **params):
        book2page_result = dict()
        books_info_conf = params.get('conf', {}).get('books_info_conf')
        books_info_conf = module_path + books_info_conf
        self.load_concepts()
        book2book_info = self.load_books_info(books_info_conf)
        # 对语料进行标号，教科书按章节划分，论文成篇划分。
        self.mark_chapter_idx(books, book2book_info)
        import pdb;pdb.set_trace()
        for book in books:
            book_info = book2book_info.get(book)
            book2page_result[book] = self.count_one(book, book_info)
        # 储存原始数据
        import pdb;pdb.set_trace()
        self.save_data(book2page_result, book2book_info)



def main():
    books = ['1L2RM', 'StatisticalModels', 'ComputationalStatistics']
    dealer = ConceptIdxDealer()
    concepts = dealer.run(books)
    print(concepts)
    return concepts


if __name__ == '__main__':
    main()
