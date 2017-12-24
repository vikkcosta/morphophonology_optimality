from feature_table import FeatureTable
from constraint_set import ConstraintSet
from grammar import Grammar
from lexicon import Lexicon, Word
from hypothesis import Hypothesis
from hmm import INITIAL_STATE, FINAL_STATE, HMM
from corpus import Corpus
from configuration import Configuration
from tests.persistence_tools import get_feature_table_fixture, get_constraint_set_fixture
from debug_tools import print_empty_line, write_to_dot as dot
from utils import get_configuration, create_flag
from constraint import FeatureBundle, PhonotacticConstraint
from random import random, randint, choice

configurations_dict = {
    "ALLOW_CANDIDATES_WITH_CHANGED_SEGMENTS": True,
    "DATA_ENCODING_LENGTH_MULTIPLIER": 100,
    "GRAMMAR_ENCODING_LENGTH_MULTIPLIER": 1,
    "CORPUS_DUPLICATION_FACTOR": 1,

}

configuration = Configuration()
configuration.load_configurations_from_dict(configurations_dict)

feature_table = FeatureTable.load(get_feature_table_fixture("vowel_harmony_simple_feature_table.json"))
print(feature_table)

initial_constraint_set = ConstraintSet.load(get_constraint_set_fixture("vowel_harmony_permuted_constraint_set.json"))
target_constraint_set = ConstraintSet.load(get_constraint_set_fixture("vowel_harmony_simple_constraint_set.json"))

target_stems = ["unu", "uku", "nunu", "kunu", "nuku", "kuku",
                "ini", "iki", "nini", "kini", "niki", "kiki"]

underlying_suffixes = ["kun"]
surface_suffixes = ["kun", "kin"]


def _get_anchor_vowel(word):
    if "i" in word:
        return "i"
    elif "u" in word:
        return "u"
    else:
        return ValueError("no anchor vowel found (i, u)")


def get_target_stems_and_suffixes(stems, suffixes):
    result = []
    for stem in stems:
        stem_anchor_vowel = _get_anchor_vowel(stem)
        for suffix in suffixes:
            if stem_anchor_vowel in suffix:
                stem_and_suffix = "{}{}".format(stem, suffix)
                result.append(stem_and_suffix)
    return result


target_stems_and_suffixes = get_target_stems_and_suffixes(target_stems, surface_suffixes)


corpus = target_stems + target_stems_and_suffixes
corpus = Corpus(corpus)


data = corpus.get_words()
max_word_length_in_data = max([len(word) for word in data])

#initial hypothesis

initial_lexicon = Lexicon(data, max_word_length_in_data)
initial_grammar = Grammar(initial_constraint_set, initial_lexicon)
initial_hypothesis = Hypothesis(initial_grammar, data)
initial_energy = initial_hypothesis.get_energy()
print(f"initial hypothesis: {initial_hypothesis.get_recent_energy_signature()}")
print(f"initial energy: {initial_energy}")
print_empty_line()


target_hmm_transitions = {INITIAL_STATE: ["q1"],
                          "q1": ["q2", FINAL_STATE],
                          "q2": [FINAL_STATE]}

target_hmm_emissions = {"q1": target_stems,
                        "q2": ["kun"]}

target_hmm_inner_states = ["q1", "q2"]
target_hmm = HMM(target_hmm_transitions, target_hmm_emissions, target_hmm_inner_states)
target_lexicon = Lexicon([], max_word_length_in_data, initial_hmm=target_hmm)
target_grammar = Grammar(target_constraint_set, target_lexicon)
target_hypothesis = Hypothesis(target_grammar, data)
target_energy = target_hypothesis.get_energy()
print(f"target hypothesis: {target_hypothesis.get_recent_energy_signature()}")
print(f"target/initial delta (should be negative): {target_energy-initial_energy}")
# dot(initial_lexicon.hmm, "vowel_harmony_initial_hmm")
# dot(target_lexicon.hmm, "vowel_harmony_target_hmm")

# for constraint in initial_constraint_set.constraints:
#     print(constraint.feature_bundles)

