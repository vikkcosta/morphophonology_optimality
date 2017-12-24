import logging
from math import log, ceil
from random import choice, randint

from utils import get_configuration, get_feature_table, get_weighted_list
from word import Word
from hmm import HMM

logger = logging.getLogger(__name__)


class Lexicon:
    def __init__(self, string_input_words, max_word_length_in_data, initial_hmm=None, alphabet_or_words="words"):
        if not isinstance(string_input_words, list):
            raise ValueError("should be list")
        self.feature_table = get_feature_table()
        self.max_word_length_in_data = max_word_length_in_data
        if not initial_hmm:
            feature_table = get_feature_table()
            if alphabet_or_words == "alphabet":
                alphabet = feature_table.get_alphabet()
                self.hmm = HMM.create_hmm_alphabet(alphabet)
            elif alphabet_or_words == "words":
                self.hmm = HMM.create_hmm_from_list(string_input_words)
        else:
            self.hmm = initial_hmm

        self.words = []
        self._update_words()

    def make_mutation(self):
        mutation_result = self.hmm.make_mutation()
        if mutation_result:
            self._update_words()
        return mutation_result

    def get_encoding_length(self):
        hmm_encoding_length = self.hmm.get_encoding_length()
        return hmm_encoding_length

    def get_distinct_segments(self):
        distinct_segments = set()
        for word in self.words:
            distinct_segments = distinct_segments | set(word.get_segments())
        return distinct_segments

    def get_number_of_distinct_words(self):
        return len(set(self.words))

    def _get_number_of_segments(self):
        return sum([len(word) for word in self.words])

    def get_words(self):
        return self.words

    def _update_words(self):
        string_words = self.hmm.get_string_words_up_to_length(self.max_word_length_in_data)
        updated_words = [Word(string_word) for string_word in string_words]
        self.words = updated_words

    def __str__(self):
            return "Lexicon, number of words: {0}, number of segments: {1}".format(len(self.words),
                                                                         self._get_number_of_segments())

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.words[item].get_segments()

    def __len__(self):
        return len(self.words)
