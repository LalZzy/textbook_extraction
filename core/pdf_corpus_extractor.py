# -*- coding: utf-8 -*-

import io
import re
import json
import os
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from concurrent.futures import ThreadPoolExecutor

ReplaceDict = {
    'ﬁ': 'fi',
    'ﬂ': 'fl',
    'ﬀ': 'ff',
    'ﬃ': 'ffi',
    'ﬄ': 'ffl',
    '−': '-',
    '–': '-'
}

class PdfCorpusExtractor(object):
    def __init__(self, force_create=False):
        self.force_create = force_create

    def run(self, books, **params):
        with ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(
                self.run_one,
                books
            )

    def run_one(self, book):
        module_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        pdf_file = module_path + '/data/corpus/' + book + '.pdf'
        json_file = module_path + '/data/corpus/' + book + '.json'
        if not os.path.exists(json_file) or self.force_create:
            print('{} output json file does not exist. generating one.'.format(book))
            self.generate_output(pdf_file, json_file)
        print('{}: finish deal book {}, already generate json file.'.format(
            self.__class__.__name__, book))

    def generate_output(self, pdf_file, json_file):
        res = {}
        counter = 1

        for page in self.extract_text_by_page(pdf_file):
            text = re.sub("\x0c", ' ', page)
            # 连字符深恶痛绝！
            for f_word, t_word in ReplaceDict.items():
                text = text.replace(f_word, t_word)
            # 把文本全部转化为小写
            res[counter] = text.lower()
            counter += 1
        res['total_pages'] = counter
        with open(json_file, 'w') as fh:
            json.dump(res, fh)

    def extract_text_by_page(self, pdf_path):
        with open(pdf_path, 'rb') as fh:
            for page in PDFPage.get_pages(fh,
                                          caching=True,
                                          check_extractable=True):
                resource_manager = PDFResourceManager()
                fake_file_handle = io.StringIO()
                # 保留原文件中的空格
                laparams = LAParams()
                converter = TextConverter(
                    resource_manager, fake_file_handle, laparams=laparams)
                page_interpreter = PDFPageInterpreter(
                    resource_manager, converter)
                page_interpreter.process_page(page)

                text = fake_file_handle.getvalue()
                yield text

                # close open handles
                converter.close()
                fake_file_handle.close()

    def extract_text(self, pdf_path):
        result = []
        for page in self.extract_text_by_page(pdf_path):
            result.append(re.sub("\x0c", ' ', page))
        return result

    def extract_outline(self, pdf_path):
        # Open a PDF document.
        fp = open(pdf_path, 'rb')
        parser = PDFParser(fp)
        document = PDFDocument(parser)
        # Get the outlines of the document.
        outlines = document.get_outlines()
        # print(list(outlines))
        result = [(level, title) for (level, title, dest, a, se) in outlines]
        return result


if __name__ == '__main__':
    books = ['1L2RM']
    dealer = PdfCorpusExtractor(force_create=True)
    dealer.run(books)
