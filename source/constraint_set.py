import json
import logging
import pickle

from io import StringIO

from random import choice, randrange
from constraint import Constraint, get_number_of_constraints
from transducer import Transducer
from constraint import MaxConstraint, DepConstraint, PhonotacticConstraint, IdentConstraint
from utils import get_configuration, get_feature_table, get_feature_table, get_weighted_list, ceiling_of_log_two

logger = logging.getLogger(__name__)

constraints_delimiter_for_printing = " >> "

constraint_set_transducers = dict()

demote_caching_flag = True


class ConstraintSet:
    def __init__(self, constraint_set_list):
        self.feature_table = get_feature_table()
        self.constraints = list()
        for constraint in constraint_set_list:
            constraint_name = constraint["type"]
            bundles_list = constraint["bundles"]
            if not constraint_name:
                raise ValueError("Missing 'type' key")

            constraint_class = Constraint.get_constraint_class_by_name(constraint_name)
            self.constraints.append(constraint_class(bundles_list))

    def get_encoding_length(self):
        k = ceiling_of_log_two(get_number_of_constraints() + self.feature_table.get_number_of_features() + 2 + 1)
        return k * (1 + sum([constraint.get_encoding_length() for constraint in self.constraints]))

    def make_mutation(self):
        mutation_weights = [(self._insert_constraint, get_configuration("INSERT_CONSTRAINT")),
                            (self._remove_constraint, get_configuration("REMOVE_CONSTRAINT")),
                            (self._demote_constraint, get_configuration("DEMOTE_CONSTRAINT")),
                            (self._insert_feature_bundle_phonotactic_constraint, get_configuration("INSERT_FEATURE_BUNDLE_PHONOTACTIC_CONSTRAINT")),
                            (self._remove_feature_bundle_phonotactic_constraint, get_configuration("REMOVE_FEATURE_BUNDLE_PHONOTACTIC_CONSTRAINT")),
                            (self._augment_feature_bundle, get_configuration("AUGMENT_FEATURE_BUNDLE"))]

        weighted_mutation_function_list = get_weighted_list(mutation_weights)
        return choice(weighted_mutation_function_list)()

    def _remove_constraint(self):
        logger.debug("_remove_constraint")
        if len(self.constraints) > get_configuration("MIN_NUMBER_OF_CONSTRAINTS_IN_CONSTRAINT_SET"):
            removable_constraints = list(filter(lambda x: x.get_constraint_name() != "Faith", self.constraints))
            self.constraints.remove(choice(removable_constraints))
            return True
        else:  # can not remove constraint, resulting constraint_set length will br beneath minimum length
            return False

    def _insert_feature_bundle_phonotactic_constraint(self):
        """
        insert a feature bundle in a Phonotactic constraint
        """
        logger.debug("_insert_feature_bundle_phonotactic_constraint")
        phonotactic_constraints = list(filter(lambda x: x.get_constraint_name() == "Phonotactic", self.constraints))
        if phonotactic_constraints:
            if choice(phonotactic_constraints).insert_feature_bundle():
                return True
            else:  # augment_constraint did not succeed
                return False
        else:  # there no phonotactic constraints to update
            return False

    def _remove_feature_bundle_phonotactic_constraint(self):
        """
        removes a feature bundle from  a Phonotactic constraint
        """
        logger.debug("_remove_feature_bundle_phonotactic_constraint")
        phonotactic_constraints = list(filter(lambda x: x.get_constraint_name() == "Phonotactic", self.constraints))
        if phonotactic_constraints:
            if choice(phonotactic_constraints).remove_feature_bundle():
                return True
            else:  # augment_constraint did not succeed
                return False
        else:  # there no phonotactic constraints to update
            return False

    def _augment_feature_bundle(self):
        logger.debug("_augment_feature_bundle")
        augmentable_constraints = list(filter(lambda x: x.get_constraint_name() != "Faith", self.constraints))
        if augmentable_constraints:
            if choice(augmentable_constraints).augment_feature_bundle():
                return True
            else:  # augment_feature_bundle did not succeed
                return False

    def _demote_constraint(self):
        """
        The highet ranking constraint is at index 0
        """
        logger.debug("_demote_constraint")
        if len(self.constraints) > 1:

            if demote_caching_flag:
                transducer = pickle.loads(pickle.dumps(self.get_transducer(), -1))

            index_of_demotion = randrange(len(self.constraints)-1)  # index of a random constraint
            i = index_of_demotion                                      # (which is not the lowest ranked)
            j = index_of_demotion+1  # index of the constraint lower by 1
            self.constraints[i], self.constraints[j] = self.constraints[j], self.constraints[i]  # swap places

            if demote_caching_flag:
                transducer.swap_weights_on_arcs(index_of_demotion, index_of_demotion+1)
                constraint_set_transducers[str(self)] = transducer

            return True
        else:
            return False

    def _insert_constraint(self):
        logger.debug("_insert_constraint")
        if len(self.constraints) < get_configuration("MAX_NUMBER_OF_CONSTRAINTS_IN_CONSTRAINT_SET"):
            mutation_weights_for_insert = [(DepConstraint, get_configuration("DEP_FOR_INSERT")),
                                           (MaxConstraint, get_configuration("MAX_FOR_INSERT")),
                                           (IdentConstraint, get_configuration("IDENT_FOR_INSERT")),
                                           (PhonotacticConstraint, get_configuration("PHONOTACTIC_FOR_INSERT"))]

            weighted_constraint_class_for_insert = get_weighted_list(mutation_weights_for_insert)

            new_constraint_class = choice(weighted_constraint_class_for_insert)
            new_constraint = new_constraint_class.generate_random()
            index_of_insertion = randrange(len(self.constraints)+1)
            if new_constraint in self.constraints:  # newly generated constraint is already in constraint_set
                return False
            else:
                self.constraints.insert(index_of_insertion, new_constraint)
                return True
        else:
            return False

    def get_transducer(self):
        constraint_set_key = str(self)
        if constraint_set_key in constraint_set_transducers:
            return constraint_set_transducers[constraint_set_key]
        else:
            transducer = self._make_transducer()
            constraint_set_transducers[constraint_set_key] = transducer
            return transducer

    def _make_transducer(self):
        if len(self.constraints) is 1:                             # if there is only on constraint in the
            return pickle.loads(pickle.dumps(self.constraints[0].get_transducer(), -1))  # constraint set there is no need to intersect
        else:
            constraints_transducers = [constraint.get_transducer() for constraint in self.constraints]
            return Transducer.intersection(*constraints_transducers)

    @staticmethod
    def clear_caching():
        global constraint_set_transducers
        constraint_set_transducers = dict()

    @classmethod
    def loads(cls, constraint_set_json_str):
        constraint_set_list = json.loads(constraint_set_json_str)
        return cls(constraint_set_list)

    @classmethod
    def load(cls, constraint_set_file_name):

        with open(constraint_set_file_name, "r") as f:
            file_string = f.read()
            try:
                constraint_set_list = json.loads(file_string)
            except ValueError:
                return ConstraintSet.load_from_printed_string_representation(file_string)
        return cls(constraint_set_list)

    @classmethod
    def load_from_printed_string_representation(cls, constraint_set_string):
        constraint_set_json_str = cls.json_from_printed_string_representation(constraint_set_string)
        constraint_set_list = json.loads(constraint_set_json_str)
        return cls(constraint_set_list)

    @classmethod
    def json_from_printed_string_representation(cls, constraint_set_string):
        '''
        dict order of features in bundle in irrelevant
        '''
        #Phonotactic[[+stop][+syll]]

        #Phonotactic[[+stop, -voice][+syll]]
        #{"type": "Phonotactic", "bundles": [{"stop": "+", "voice": "-"}, {"syll": "+}]}

        #Faith[] >> Phonotactic[+cons] >> Max[+cons]

        constraint_set_list = list()
        string_constraints = constraint_set_string.split(constraints_delimiter_for_printing)
        for string_constraint in string_constraints:
            constraint_set_list.append(_parse_constraint(string_constraint))

        constraint_set_json = str(constraint_set_list).replace("'", '"') # ' -> "
        return constraint_set_json

    def __str__(self):
        string_io = StringIO()
        print("Constraint Set: ", file=string_io, end="")
        for i, constraint in enumerate(self.constraints):
            if i != 0:
                print(constraints_delimiter_for_printing, file=string_io, end="")
            print("{0}".format(constraint), file=string_io, end="")
        return string_io.getvalue()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(str(self))


def _parse_bundle(bundle_string):
    # [+stop, -voice]  -> {"stop": "+", "voice": "-"}
    # [+syll]  - > {"syll": "+}
    bundle_dict = dict()
    if bundle_string.count("[") > 0:
        bundle_string = bundle_string[1:-1]  # remove surrounding []
    features = bundle_string.split(", ")
    for feature_string in features:
        bundle_dict[feature_string[1:]] = feature_string[0]
    return bundle_dict


def _parse_bundle_list(bundle_list_string):
    #  [[+stop, -voice][+syll]] -> [{"stop": "+", "voice": "-"}, {"syll": "+}]
    bundle_list = list()
    if bundle_list_string == "[]":
        return list()
    bundle_list_string = bundle_list_string[1:-1]  # remove surrounding []
    bundle_list_string = bundle_list_string.replace("][", "]|[")  # [+stop, -voice][+syll] -> [+stop, -voice]|[+syll]
    for bundle_string in bundle_list_string.split("|"):
        bundle_list.append(_parse_bundle(bundle_string))
    return bundle_list


def _parse_constraint(constraint_string):
    constraint_dict = dict()
    constraint_string = constraint_string.replace("[","|[",1)
    split_ = constraint_string.split("|")
    constraint_name = split_[0]
    constraint_bundle_list = split_[1]

    constraint_dict["type"] = constraint_name
    constraint_dict["bundles"] = _parse_bundle_list(constraint_bundle_list)

    return constraint_dict



