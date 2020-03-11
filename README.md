# TextbookExtraction

## introduction

Using pdfminer, a python library, to extract key concept from several books.

## how to use 

run scripts to install required packages.

required python version: python3

```shell
pip install -r requirement.txt
```

before your run the program, you need to:

(1) put all books in ./data/corpus/ , you'd better use a clear file name: bookname.pdf.

(2) put all defined concept pair file in ./data/concepts/ , each file named as concepts_bookname.xlsx

then write your conf file in ./conf, you can reference ./conf/task_conf.yaml and ./conf/books_info.yaml.

when everything is ok, run 

```shell
python main.py 
```

The output will be:

./data/concepts/all_concepts.csv record concept-concept_idx relation.
./data/concepts/book_chapter_ids.csv record chapter-chapter_idx relation.
./data/concepts_page_nums/all_words_info.csv with format: (book_idx,course_idx,fre)

## tools

you can use this tool to transform output data to more readable format.
```shell
cd tools
python get_word_stat_info.py --word_idx xxx
# or
python get_word_stat_info.py --word 
```





