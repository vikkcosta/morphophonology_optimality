import logging
import pickle



from parser import ParsingNFA
from utils import get_configuration, get_feature_table, ceiling_of_log_two
from typing import Dict, Set, Tuple

logger = logging.getLogger(__name__)


class Hypothesis:
    def __init__(self, grammar, data):
        self.grammar = grammar
        self.data = data
        self.data_parse_dict = None
        self.grammar_energy = None
        self.data_energy = None
        self.combined_energy = None

    def get_energy(self):
        data_length = self.get_data_length_given_grammar()
        grammar_length = self.grammar.get_encoding_length()
        data_multiplier = get_configuration("DATA_ENCODING_LENGTH_MULTIPLIER")
        grammar_multiplier = get_configuration("GRAMMAR_ENCODING_LENGTH_MULTIPLIER")
        self.grammar_energy = grammar_length * grammar_multiplier
        self.data_energy = data_length * data_multiplier
        self.combined_energy = self.grammar_energy + self.data_energy
        return self.combined_energy

    def get_data_length_given_grammar(self):
        """data_parse_dict is a dictionary with:
            keys: words of the data;
            values: sets of parses of a word [parse = a pair (underlying_form, number_of_surface_forms)]"""

        data_parse_dict: Dict[str, Set[Tuple[str, int]]] = self.parse_data()
        for surface_form in self.data:
            if not data_parse_dict[surface_form]:  # if data_parse_dict[word] is the empty set
                return float("inf")

        self.data_parse_dict = data_parse_dict

        fado_nfa = self.grammar.lexicon.hmm.nfa
        parsing_nfa = ParsingNFA.get_from_fado_nfa(fado_nfa)

        encoding_length = 0
        for target_surface_form in self.data:
            combined_choice_encoding_lengths_list = []
            for underlying_form_tuple in data_parse_dict[target_surface_form]:
                underlying_form, number_of_surface_forms_derived_from_underlying_form = underlying_form_tuple
                underlying_form_choice_encoding_length = parsing_nfa.get_observation_encoding_length(str(underlying_form))
                surface_form_choice_encoding_length = ceiling_of_log_two(number_of_surface_forms_derived_from_underlying_form)
                combined_choice_encoding_length = underlying_form_choice_encoding_length + surface_form_choice_encoding_length
                combined_choice_encoding_lengths_list.append(combined_choice_encoding_length)
            minimal_combined_choice_encoding_length = min(combined_choice_encoding_lengths_list)
            encoding_length += minimal_combined_choice_encoding_length
        return encoding_length

    def get_recent_data_parse(self):
        result = ""
        data_parse_with_string_keys = dict()
        for word in self.data_parse_dict:
            data_parse_with_string_keys[str(word)] = self.data_parse_dict[word]

        word_list = [word for word in data_parse_with_string_keys]
        word_list.sort(key=lambda item: (len(item), item))   # sort by length first and then alphabetically
        for output_word in word_list:
            parse_set = data_parse_with_string_keys[output_word]
            for parse in parse_set:
                input_word = parse[0]
                number_of_outputs = parse[1]
                if str(input_word) != output_word:
                    result += "{} --> {} ({}) # ".format(input_word, output_word, number_of_outputs)

        if len(result):
            result = result[:-3]  # remove final delimiter

        return result

    def get_recent_energy_signature(self):
        return "Energy: {:,} bits (Grammar = {:,}) + (Data = {:,})".format(self.combined_energy, self.grammar_energy,
                                                                           self.data_energy)

    def parse_data(self):
        """ Parses Words

        :param data: Words to be parsed, usually it will parse the corpus words
        :type data: a list of Words
        :rtype: A dictionary that has the Words in data as keys and the values are sets of tuples. Each tuple
        contains (Word, int) which the Word is able to generate the Word in the key of the dictionary and
        the int is the number of outputs that the Word can generate.

        A word that not able to parsed will return an empty set in the value of the word
        entry in the dictionary.

        The number of outputs an input can generate is later used to calculate the probability of a word under
        the grammar.
        """
        data_parse_dict = {word: set() for word in self.data}
        lexicon_word_set = set(self.grammar.lexicon.get_words())


        for word_in_lexicon in lexicon_word_set:
            outputs = self.grammar.generate(word_in_lexicon)  # outputs in a list of Words
            number_of_outputs = len(outputs)
            for output in outputs:
                if output in self.data:
                    parse = (word_in_lexicon, number_of_outputs)
                    data_parse_dict[output].add(parse)
        # print(data_parse_dict)
        return data_parse_dict

    def get_neighbor(self):
        new_hypothesis = self.get_hypothesis_copy()
        mutation_result = new_hypothesis.grammar.make_mutation()
        return mutation_result, new_hypothesis

    def get_hypothesis_copy(self):
        grammar_copy = pickle.loads(pickle.dumps(self.grammar, -1))
        return Hypothesis(grammar_copy, self.data)

    def __str__(self):
        return "Hypothesis with energy: {0}".format(self.get_energy())

    def __repr__(self):
        return self.__str__()

