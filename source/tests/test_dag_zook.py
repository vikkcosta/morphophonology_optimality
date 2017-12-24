from feature_table import FeatureTable
from constraint_set import ConstraintSet
from grammar import Grammar
from lexicon import Lexicon
from hypothesis import Hypothesis
from hmm import INITIAL_STATE, FINAL_STATE, HMM
from corpus import Corpus
from configuration import Configuration
from tests.persistence_tools import get_feature_table_fixture, get_constraint_set_fixture
from debug_tools import print_empty_line, write_to_dot as dot

configurations_dict = {
    "ALLOW_CANDIDATES_WITH_CHANGED_SEGMENTS": True,
    "DATA_ENCODING_LENGTH_MULTIPLIER": 25,
    "GRAMMAR_ENCODING_LENGTH_MULTIPLIER": 1,
    "CORPUS_DUPLICATION_FACTOR": 1,
}

configuration = Configuration()
configuration.load_configurations_from_dict(configurations_dict)

feature_table = FeatureTable.load(get_feature_table_fixture("plural_english_feature_table.json"))

initial_constraint_set = ConstraintSet.load(get_constraint_set_fixture("dag_zook_devoicing_permutations_constraint_set.json"))
target_constraint_set = ConstraintSet.load(get_constraint_set_fixture("dag_zook_devoicing_constraint_set.json"))

target_stems = ['dag', 'kat', 'dot', 'kod', 'gas', 'toz', 'ata', 'aso']

# suffixes -  underlying representation: "zook", "gos" and "dod" (+ surface forms: "sook", "kos" and "tod")

target_stems_and_suffixes = ['dagdod', 'daggos', 'dagzook',
                             'kattod', 'katkos', 'katsook',
                             'dottod', 'dotkos', 'dotsook',
                             'koddod', 'kodgos', 'kodzook',
                             'gastod', 'gaskos', 'gassook',
                             'tozdod', 'tozgos', 'tozzook',
                             'atadod', 'atagos', 'atazook',
                             'asodod', 'asogos', 'asozook']


corpus = target_stems + target_stems_and_suffixes
corpus = Corpus(corpus)


data = corpus.get_words()
max_word_length_in_data = max([len(word) for word in data])

#initial hypothesis

initial_lexicon = Lexicon(data, max_word_length_in_data)
dot(initial_lexicon.hmm, 'dagzook_initial_hmm')
initial_grammar = Grammar(initial_constraint_set, initial_lexicon)
initial_hypothesis = Hypothesis(initial_grammar, data)
initial_energy = initial_hypothesis.get_energy()
print(f"initial hypothesis: {initial_hypothesis.get_recent_energy_signature()}")
print(f"initial energy: {initial_energy}")
print_empty_line()


target_hmm_transitions = {INITIAL_STATE: ['q1'],
                          'q1': ['q2', FINAL_STATE],
                          'q2': [FINAL_STATE]}

target_hmm_emissions = {'q1': target_stems,
                        'q2': ['zook', 'gos', 'dod']}

target_hmm_inner_states = ['q1', 'q2']
target_hmm = HMM(target_hmm_transitions, target_hmm_emissions, target_hmm_inner_states)
target_lexicon = Lexicon([], max_word_length_in_data, initial_hmm=target_hmm)
target_grammar = Grammar(target_constraint_set, target_lexicon)
target_hypothesis = Hypothesis(target_grammar, data)
target_energy = target_hypothesis.get_energy()
print(f"target hypothesis: {target_hypothesis.get_recent_energy_signature()}")
print(f"target/initial delta (should be negative): {target_energy-initial_energy}")
