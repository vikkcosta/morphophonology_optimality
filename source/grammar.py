import inspect
import logging
from random import choice

from debug_tools import write_to_dot as dot
from transducer import Transducer
from transducers_optimization_tools import optimize_transducer_grammar_for_word, make_optimal_paths
from utils import get_configuration, get_feature_table, get_weighted_list

logger = logging.getLogger(__name__)

outputs_by_constraint_set_and_word = dict()

grammar_transducers = dict()


class Grammar:
    def __init__(self, constraint_set, lexicon):
        self.feature_table = get_feature_table()
        self.constraint_set = constraint_set
        self.lexicon = lexicon

    def get_encoding_length(self):
        return self.constraint_set.get_encoding_length() + self.lexicon.get_encoding_length()

    def make_mutation(self):
        mutation_weights = [(self.lexicon, get_configuration("MUTATE_LEXICON")),
                            (self.constraint_set, get_configuration("MUTATE_CONSTRAINT_SET"))]

        weighted_mutatable_object_list = get_weighted_list(mutation_weights)
        object_or_method = choice(weighted_mutatable_object_list)
        if inspect.ismethod(object_or_method):
            method = object_or_method
            mutation_result = method()
        else:
            object_ = object_or_method
            mutation_result = object_.make_mutation()
        return mutation_result

    def get_transducer(self):
            constraint_set_key = str(self.constraint_set) # constraint_set is the identifier of the grammar transducer
            if constraint_set_key in grammar_transducers:
                return grammar_transducers[constraint_set_key]
            else:
                transducer = self._make_transducer()
                grammar_transducers[constraint_set_key] = transducer
                return transducer

    def _make_transducer(self):
        constraint_set_transducer = self.constraint_set.get_transducer()
        try:
            make_optimal_paths_result = make_optimal_paths(constraint_set_transducer)
        except Exception as ex:
            logger.error("make_optimal_paths failed. transducer dot are being printed")
            #write_to_dot(constraint_set_transducer,"constraint_set_transducer")
            for constraint in self.constraint_set.constraints:
                dot(constraint.get_transducer(), str(constraint))
            raise ex

        return make_optimal_paths_result

    def generate(self, word):
        constraint_set_and_word_key = str(self.constraint_set) + str(word)
        if constraint_set_and_word_key in outputs_by_constraint_set_and_word:
            return outputs_by_constraint_set_and_word[constraint_set_and_word_key]
        else:
            outputs = self._get_outputs(word)
            outputs_by_constraint_set_and_word[constraint_set_and_word_key] = outputs
            return outputs

    def _get_outputs(self, word):
        grammar_transducer = self.get_transducer()
        word_transducer = word.get_transducer()
        intersected_transducer = Transducer.intersection(word_transducer,    # a transducer with NULLs on inputs and JOKERs on outputs
                                                         grammar_transducer) # a transducer with segments on inputs and sets on outputs

        intersected_transducer.clear_dead_states()
        intersected_transducer = optimize_transducer_grammar_for_word(word, intersected_transducer)
        #dot(intersected_transducer, 'intersected')
        outputs = intersected_transducer.get_range()
        return outputs

    def __str__(self):
        return "Grammar with [{0}]; and [{1}]".format(self.constraint_set, self.lexicon)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(str(self))

    @staticmethod
    def clear_caching():
            global outputs_by_constraint_set_and_word
            outputs_by_constraint_set_and_word = dict()

            global grammar_transducers
            grammar_transducers = dict()