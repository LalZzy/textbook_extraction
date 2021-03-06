# -*- coding: utf-8 -*-
import re
import os
import yaml
import json
import csv
from collections import defaultdict, Counter
import sys
import xlrd
from pattern.text.en import pluralize, singularize
import logging
logging.basicConfig(level=logging.INFO)

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cpts_with_single_name = set()
cpts_with_multi_name = set()
inverted_index = defaultdict(list)
DEFAULT_BOOK_INFO = {
  'document_st_page': 1,
  'document_end_page': 1,
  'chapter_pages': [1,2]
}

class ConceptIdxDealer(object):
    def __init__(self, need_update=True):
        self.need_update = need_update
        self.inversed_index = {}
        self.forward_index = {}
        self.concept2idx = {}
        self.cpts_len = 0
        self.concepts_rw_path = module_path + '/data/concepts/'

    def read_one_file(self, book):
        data_list = []
        possible_fps = [self.concepts_rw_path + 'concept_' + book + '.xlsx',
                        self.concepts_rw_path + 'concept_' + book + '.csv']
        if os.path.exists(possible_fps[0]):
            fp = possible_fps[0]
            data = xlrd.open_workbook(fp)
            table = data.sheets()[0]

            for i in range(table.nrows):
                data_list.append(table.row_values(i))
        elif os.path.exists(possible_fps[1]):
            fp = possible_fps[1]
            with open(fp) as f:
                fp_data = csv.reader(f)
                for row in fp_data:
                    data_list.append(row)
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
    
    def make_inverse_table(self, concepts, book):
        for concept in concepts:
            self.inversed_index.setdefault(concept, [])
            self.inversed_index[concept].append(book)

    def run(self, books, **params):
        for book in books:
            row = self.read_one_file(book)
            for concepts in row:
                concepts = [concept.lower() for concept in concepts if concept != '']
                concepts = [concept.replace('–', '-').replace('−', '-') for concept in concepts]
                concepts = [singularize(concept) for concept in concepts]
                self.mark_idx(concepts)
                self.make_inverse_table(concepts, book)
        if self.need_update:
            with open(self.concepts_rw_path + 'all_concepts.csv', 'w+') as f:
                for concept, idx in sorted(self.concept2idx.items(), key=lambda x: x[1]):
                    f.write('{}::{}\n'.format(concept, idx))
            with open(self.concepts_rw_path + 'concepts_book_inverse_table.csv','w+') as f:
                for concept, books in self.inversed_index.items():
                    for book in books:
                        f.write('{}::{}\n'.format(concept, book))
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
        document_text = [i.replace('\n', ' ') for i in document_text]

        page_result = dict()
        for concept, idx in self.concept2idx.items():
            page2frequency = self.count_one_concept(concept, document_text)
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
                chapter_idx = self.book_chapter2idx.get(book).get(i+1)
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
                        f.write('{},{},{}\n'.format(chp, concept, frequency))

    def count_one_concept(self, concept, document_text):
        record = []

        # '(' ,')'是正则表达式中的元字符，所以要把查询pattern中的'('替换为'\('
        concept = concept.replace('(', '\(').replace(')', '\)')
        # 处理单复数匹配
        word_pages_fre = [len(re.findall(r'\b({}|{})\b'.format(
            concept, pluralize(concept)), text)) for text in document_text]
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
            book_conf = books_info_conf.get(book) or DEFAULT_BOOK_INFO
            chapter_info = book_conf.get('chapter_pages')
            for i, _ in enumerate(chapter_info[:-1]):
                mark[i+1] = idx
                idx += 1
            self.book_chapter2idx[book] = mark
        with open(module_path + '/data/concepts/book_chapter_ids.csv', 'w+') as fw:
            for book in books:
                chapter2idx = self.book_chapter2idx.get(book)
                for i, idx in chapter2idx.items():
                    fw.write('{},{}\n'.format(str(i)+book, str(idx)))
        
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
        for book in books:
            book_info = book2book_info.get(book) or DEFAULT_BOOK_INFO
            book2page_result[book] = self.count_one(book, book_info)
            logging.warning('{} finish deal book {}'.format(self.__class__.__name__, book))
        # 储存原始数据
        self.save_data(book2page_result, book2book_info)

class ConceptStatisticDealer(object):
    
    def __init__(self):
        self.stat_file = module_path + '/data/concept_page_nums/all_words_info.csv'
        self.concept_name_file = module_path + '/data/concepts/all_concepts.csv'
        self.stat_write_file = module_path + '/data/concepts/concepts_stat.csv'
    
    def run(self, books, **params):
        stats = defaultdict(int)
        idx2concept = dict()
        with open(self.concept_name_file, 'r') as f:
            for i in f:
                concept, idx = i.strip().split('::')
                idx2concept[idx] = concept
                
        for i in idx2concept.values():
            stats[i] += 0

        with open(self.stat_file, 'r') as f:
            for i in f:
                _, concept_idx, count = i.strip().split(',')
                stats[idx2concept.get(concept_idx)] += int(count)
        
        with open(self.stat_write_file, 'w') as f:
            for concept, count in sorted(stats.items(), key=lambda x: x[1]):
                f.write('{}::{}\n'.format(concept, count))
        return None
                

def main():
    books = ['1L2RM', 'StatisticalModels', 'ComputationalStatistics']
    dealer = ConceptIdxDealer()
    # dealer = ConceptStatisticDealer()
    concepts = dealer.run(books)
    print(concepts)
    return concepts

def test_read_concepts():
    books = ['1L2RM', 'ExtremalMechanismsforLocalDifferentialPrivacy']
    dealer = ConceptIdxDealer()
    for book in books:
        concepts = dealer.read_one_file(book)
        print(concepts)
        

if __name__ == '__main__':
    main()
    # test_read_concepts()
