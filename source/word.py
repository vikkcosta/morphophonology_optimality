import logging
from random import randint, choice
from segment import Segment, NULL_SEGMENT, JOKER_SEGMENT
from transducer import Transducer, State, Arc, CostVector
from utils import get_feature_table
from debug_tools import write_to_dot as dot

word_transducers = dict()


class Word:
    __slots__ = ["word_string", "feature_table", "segments"]

    def __init__(self, word_string):
        """word_string and segment should be in sync at any time"""
        self.feature_table = get_feature_table()
        self.word_string = word_string
        self.segments = [Segment(char) for char in self.word_string]

    def _set_word_string(self, new_word_string):
        self.word_string = new_word_string
        self.segments = [Segment(char, self.feature_table) for char in self.word_string]

    def get_transducer(self):
        word_key = str(self)
        if word_key in word_transducers:
            return word_transducers[word_key]
        else:
            transducer = self._make_transducer()
            word_transducers[word_key] = transducer
            return transducer

    def _make_transducer(self):
        segments = self.feature_table.get_segments()
        transducer = Transducer(segments, length_of_cost_vectors=0)
        word_segments = self.get_segments()
        n = len(self.word_string)
        states = [State("q{}".format(i), i) for i in range(n+1)]
        for i, state in enumerate(states):
            transducer.add_state(state)
            transducer.add_arc(Arc(state, NULL_SEGMENT, JOKER_SEGMENT, CostVector.get_empty_vector(), state))
            if i != n:
                transducer.add_arc(Arc(states[i], word_segments[i], JOKER_SEGMENT, CostVector.get_empty_vector(), states[i+1]))

        transducer.initial_state = states[0]
        transducer.add_final_state(states[n])
        return transducer

    def get_encoding_length(self):
        return sum(segment.get_encoding_length() for segment in self.get_segments()) + 1

    def get_segments(self):
        return self.segments

    @staticmethod
    def clear_caching():
        global word_transducers
        word_transducers = dict()

    def __str__(self):
        return self.word_string

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.word_string)

    def __eq__(self, other):
        return self.word_string == other.word_string

    def __hash__(self):
        return hash(self.word_string)