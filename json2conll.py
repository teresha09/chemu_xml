import codecs
import json
import os

from nltk.tokenize import wordpunct_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import nltk
from nltk.corpus import wordnet
from nltk import pos_tag
from tqdm import tqdm
import argparse
from bio_conll import BIO_conll

import tokenization

class Json2conll:

    def __init__(self,entity,tagger,vocab,lower_case):
        self.entity = entity
        self.tagger = tagger
        self.vocab = vocab
        self.lower_case = lower_case
        self.lemmatizer = WordNetLemmatizer()

    def get_wordnet_pos(self, treebank_tag):

        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN

    def get_token_position_in_text(self, token, w_start, text):
        delimitter_start = None
        text = text.replace('й', 'и')
        text = text.replace("ё", "е")
        while text[w_start:w_start + len(token)] != token or (delimitter_start == None and w_start != 0):
            w_start += 1
            delimitter_start = delimitter_start or w_start
        return w_start, w_start + len(token), text[delimitter_start:w_start]

    def get_bio_tag(self,w_start, w_end, entities, entity_type):
        for key, entity in entities.items():
            try:
                start = int(entity['start'])
                end = int(entity['end'])
            except Exception:
                raise Exception("Entity start and end must be an integer")

            if entity['entity'] in entity_type:
                if w_start > start and w_end <= end:
                    adding = entity['entity']
                    return 'I-' + adding
                elif w_start == start and w_end <= end:
                    adding = entity['entity']
                    return 'B-' + adding
        return '0'

    def json_to_conll(self, corpus_json_location, output_location, entity_type, by_sent=True):
        tokenizer = tokenization.FullTokenizer(
            vocab_file=self.vocab, do_lower_case=self.lower_case)
        with codecs.open(corpus_json_location, encoding='utf-8') as in_file:
            reviews = list(map(json.loads, in_file.readlines()))
            reviews = reviews[0]['data']
            f = open(corpus_json_location)
            js_data = json.load(f)
            i = 0
        with codecs.open(output_location, 'w', encoding='utf-8') as out_file:
            for review in reviews:
                documents = sent_tokenize(review['text']) if by_sent else [review['text']]
                w_start = 0
                w_end = 0
                tokens_counter = 0
                for document in documents:
                    tokens = tokenization.make_token_list(document.split(' '), tokenizer)
                    if self.tagger == "averaged_perceptron_tagger_ru":
                        pos_tags = pos_tag(tokens, lang='rus')
                    else:
                        pos_tags = pos_tag(tokens)
                    tokens_counter += len(tokens)
                    for token, temp in zip(tokens, pos_tags):
                        token_corr = temp[0].lower()
                        pos = temp[1]
                        w_start, w_end, delimitter = self.get_token_position_in_text(token, w_start, review['text'].lower())
                        bio_tag = self.get_bio_tag(w_start, w_end, review['entities'], entity_type)
                        lemm = self.lemmatizer.lemmatize(token_corr, self.get_wordnet_pos(pos))
                        out_file.write(
                            u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(token, lemm, pos, bio_tag, w_start, w_end,
                                                                       delimitter, review['index']))
                        w_start = w_end - 1
                js_data['data'][i]['n_token'] = tokens_counter
                i += 1
        os.remove(corpus_json_location)
        new_f = open(corpus_json_location, "w+")
        json.dump(js_data, new_f)

    def get_conlls(self):
        nltk.download(self.tagger)
        nltk.download('wordnet')
        train = "train.json"
        self.json_to_conll(train, "train.conll", self.entity)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-vocab", "--vocab", type=str, default="BIOBERT_DIR/vocab.txt")
    parser.add_argument('--tagger', '-tagger', type=str, default='averaged_perceptron_tagger')
    parser.add_argument('--do_lower_case', '-do_lower_case', type=bool, default=True)
    parser.add_argument("-entity", "--entity", type=str, default="reaction_product,solvent,time,temperature")
    args = parser.parse_args()
    entity = []
    for i in args.entity.split(","):
        entity.append(i)
    tagger = args.tagger
    vocab = args.vocab
    conll = Json2conll(entity, tagger, vocab, True)
    conll.get_conlls()