
from feature_table import FeatureTable
from constraint_set import ConstraintSet
from grammar import Grammar
from lexicon import Lexicon
from lexicon import Word
from configuration import Configuration
from tests.persistence_tools import get_feature_table_fixture, get_constraint_set_fixture
from simulations.dag_zook import configurations_dict
from constraint import VowelHarmonyConstraint, PhonotacticConstraint
from transducer import Transducer
from debug_tools import write_to_dot as dot

configuration = Configuration()
configuration.load_configurations_from_dict(configurations_dict)



feature_table = FeatureTable.load(get_feature_table_fixture("vowel_harmony_simple_feature_table.json"))
constraint_set = ConstraintSet.load(get_constraint_set_fixture("vowel_harmony_simple_constraint_set.json"))

data = ["unu", "uku", "nunu", "kunu", "nuku", "kuku",
        "ini", "iki", "nini", "kini", "niki", "kiki",
        "unukun", "ukukun", "nunukun", "kunukun", "nukukun", "kukukun",
        "inikin", "ikikin", "ninikin", "kinikin", "nikikin", "kikikin"]
max_word_length_in_data = max([len(word) for word in data])
lexicon = Lexicon(data, max_word_length_in_data)

grammar = Grammar(constraint_set, lexicon)
grammar_transducer = grammar.get_transducer()


underlying_forms_list = ["unu", "uku", "nunu", "kunu", "nuku", "kuku",
        "ini", "iki", "nini", "kini", "niki", "kiki",
        "unukun", "ukukun", "nunukun", "kunukun", "nukukun", "kukukun",
        "inikun", "ikikun", "ninikun", "kinikun", "nikikun", "kikikun"]
constraint_set_transducer = constraint_set.get_transducer()
# dot(constraint_set_transducer, 'tuvan_constraints_transducer')
for word in underlying_forms_list:
    word = Word(word)
    print(f"{word} --> {grammar.generate(word)}")














