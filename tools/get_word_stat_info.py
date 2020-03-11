import argparse
import os

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_data():
    idx2concept = dict()
    idx2chapter = dict()
    with open(module_path + '/data/concepts/all_concepts.csv', 'r') as f:
        for i in f:
            concept, idx = i.strip().split('::')
            idx2concept[int(idx)] = concept
    with open(module_path + '/data/concepts/book_chapter_ids.csv', 'r') as f:
        for i in f:
            chapter, idx = i.strip().split(',')
            idx2chapter[int(idx)] = chapter
    return idx2concept, idx2chapter


def summary(word_idx, word):
    freq_sum = 0
    idx2concept, idx2chapter = read_data()
    if word is not None:
        concept2idx = {v: k for k, v in idx2concept.items()}
        word_idx = concept2idx.get(word)
    print('word:{}, idx:{}\n'.format(idx2concept.get(word_idx), word_idx))
    print('chapter\tfre\n')
    with open(module_path + '/data/concept_page_nums/all_words_info.csv', 'r') as f:
        for i in f:
            chapter_idx, concept_idx, fre = map(int, i.strip().split(','))
            if concept_idx != word_idx:
                continue
            print('{}\t{}'.format(idx2chapter.get(chapter_idx), fre))
            freq_sum += fre
    print('total\t{}'.format(freq_sum))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--word_idx', type=int)
    parser.add_argument('--word')
    args = parser.parse_args()
    print(args)
    summary(args.word_idx, args.word)
