from feature_table import FeatureTable
from constraint_set import ConstraintSet
from grammar import Grammar
from lexicon import Lexicon
from hypothesis import Hypothesis
from hmm import INITIAL_STATE, FINAL_STATE, HMM, q1, q2
from corpus import Corpus
from configuration import Configuration
from tests.persistence_tools import get_feature_table_fixture, get_constraint_set_fixture
from tests.testing_utils import replace_bab_with_bb_for_everty_word
from debug_tools import write_to_dot as dot, print_empty_line


configurations_dict = {
    "ALLOW_CANDIDATES_WITH_CHANGED_SEGMENTS": False,
    "DATA_ENCODING_LENGTH_MULTIPLIER": 25,
    "GRAMMAR_ENCODING_LENGTH_MULTIPLIER": 1,
    "CORPUS_DUPLICATION_FACTOR": 1,
}

configuration = Configuration()
configuration.load_configurations_from_dict(configurations_dict)

feature_table = FeatureTable.load(get_feature_table_fixture("abnese_feature_table.json"))

faith_constraint_set = ConstraintSet.load(get_constraint_set_fixture("faith_constraint_set.json"))
target_constraint_set = ConstraintSet.load(get_constraint_set_fixture("abnese_target_constraint_set.json"))


prefix = "aab"

target_stems = ['baabab', 'babaa', 'babaab', 'bababa', 'bababab', 'baabaab', 'baaabaa', 'babaaaab', 'bababaa',
                'babababaa', "aaabab", "ababaa"]

target_prefix_and_stem_concat_only = [(prefix + stem) for stem in target_stems]
target_prefix_and_stem = [word.replace("bb", "bab") for word in target_prefix_and_stem_concat_only]  # apply rule

print(target_prefix_and_stem + target_stems)

corpus = target_stems + target_prefix_and_stem
corpus = Corpus(corpus)


data = corpus.get_words()
max_word_length_in_data = max([len(word) for word in data])


#target hypothesis
target_hmm_transitions = {INITIAL_STATE: ['q1', 'q2'], 'q1': ['q2'], 'q2': [FINAL_STATE]}
target_hmm_emissions = {'q1': [prefix], 'q2': replace_bab_with_bb_for_everty_word(target_stems)}
target_hmm_inner_states = ['q1', 'q2']
target_hmm = HMM(target_hmm_transitions, target_hmm_emissions, target_hmm_inner_states)
# dot(target_hmm, 'complex_morphology_hmm')
target_lexicon = Lexicon([], max_word_length_in_data, initial_hmm=target_hmm)
dot(target_hmm, 'abnese_target')
target_grammar = Grammar(target_constraint_set, target_lexicon)
target_hypothesis = Hypothesis(target_grammar, data)
target_energy = target_hypothesis.get_energy()
print(f"target hypothesis: {target_hypothesis.get_recent_energy_signature()}")
print_empty_line()

#words initial hypothesis

words_initial_lexicon = Lexicon(data, max_word_length_in_data, alphabet_or_words="words")
dot(words_initial_lexicon.hmm, 'abnese_initial_hmm')
words_initial_grammar = Grammar(faith_constraint_set, words_initial_lexicon)
words_initial_hypothesis = Hypothesis(words_initial_grammar, data)
words_initial_energy = words_initial_hypothesis.get_energy()
print(f"words initial hypothesis: {words_initial_hypothesis.get_recent_energy_signature()}")
print(f"target/words initial delta (should be negative): {target_energy-words_initial_energy}")
print_empty_line()
# simulation1
