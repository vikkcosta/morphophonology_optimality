import sys
from random import randint, choice
import logging
from io import StringIO
from feature_bundle import FeatureBundle
from transducer import CostVector, Arc, State, Transducer
from segment import NULL_SEGMENT, JOKER_SEGMENT, Segment
from itertools import permutations
from utils import get_configuration, get_feature_table

logger = logging.getLogger(__name__)


# A global variable that holds all the names of constraint classes that inherit from ConstraintMetaClass
_all_constraints = list()

constraint_transducers = dict()


def get_number_of_constraints():
    return len(_all_constraints)


class ConstraintMetaClass(type):
    def __new__(mcs, name, bases, attributes):
        if name != 'NewBase' and name != 'Constraint':  # NewBase is a the name of the base class used in metaclass
            _all_constraints.append(name)
        return type.__new__(mcs, name, bases, attributes)


class Constraint(metaclass=ConstraintMetaClass):
    def __init__(self, bundles_list, allow_multiple_bundles):
        """ bundle_list can contain either raw dictionaries or full blown FeatureBundle """
        self.feature_table = get_feature_table()
        if len(bundles_list) > 1 and not allow_multiple_bundles:
            raise ValueError("More bundles than allowed")

        self.feature_bundles = list()  # contain FeatureBundles

        for bundle in bundles_list:
            if type(bundle) is dict:
                self.feature_bundles.append(FeatureBundle(bundle))
            elif type(bundle) is FeatureBundle:
                self.feature_bundles.append(bundle)
            else:
                raise ValueError("Not a dict or FeatureBundle")

    def augment_feature_bundle(self):
        success = choice(self.feature_bundles).augment_feature_bundle()
        if success:
            return True
        return False

    def get_encoding_length(self):
        return 1 + sum([featureBundle.get_encoding_length() for featureBundle in self.feature_bundles]) + 1

    @classmethod
    def get_constraint_class_by_name(cls, class_name):
        this_module = sys.modules[__name__]
        for constraint_class_name in _all_constraints:
            if getattr(this_module, constraint_class_name).get_constraint_name() == class_name:
                return getattr(this_module, constraint_class_name)

    def _base_faithfulness_transducer(self):
        segments = self.feature_table.get_segments()
        transducer = Transducer(segments, name=str(self))
        state = State('q0')
        transducer.set_as_single_state(state)
        return transducer, segments, state

    @classmethod
    def generate_random(cls):
        random_feature_bundle = FeatureBundle.generate_random()
        constraint_class = Constraint.get_constraint_class_by_name(cls.get_constraint_name())
        return constraint_class([random_feature_bundle])

    def get_transducer(self):
        constraint_key = str(self)
        if constraint_key in constraint_transducers:
            return constraint_transducers[constraint_key]
        else:
            transducer = self._make_transducer()
            constraint_transducers[constraint_key] = transducer
            return transducer

    @staticmethod
    def clear_caching():
        global constraint_transducers
        constraint_transducers = dict()

    def __eq__(self, other):
        if type(self) == type(other):
            return self.feature_bundles == other.feature_bundles
        return False

    def __str__(self):
        string_io = StringIO()
        print("{0}[".format(self.get_constraint_name()), file=string_io, end="")
        for featureBundle in self.feature_bundles:
            if len(self.feature_bundles) > 1:
                print("[", file=string_io, end="")

            for i_feature, feature in enumerate(sorted(featureBundle.get_keys())):  # sorted to avoid differences in
                if i_feature != 0:                                               # implementations (esp between Py2 and
                    print(", ", file=string_io, end="")                             # Py3) - tests
                print("{0}{1}".format(featureBundle[feature], feature), file=string_io, end="")

            if len(self.feature_bundles) > 1:
                print("]", file=string_io, end="")
        print("]", file=string_io, end="")
        return string_io.getvalue()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(str(self))


class MaxConstraint(Constraint):
    def __init__(self, bundles_list):
        super(MaxConstraint, self).__init__(bundles_list, False)
        self.feature_bundle = self.feature_bundles[0]

    def _make_transducer(self):
        transducer, segments, state = super(MaxConstraint, self)._base_faithfulness_transducer()
        for segment in segments:
            transducer.add_arc(Arc(state, segment, segment, CostVector.get_vector(1, 0), state))
            transducer.add_arc(Arc(state, NULL_SEGMENT, segment, CostVector.get_vector(1, 0), state))
            if segment.has_feature_bundle(self.feature_bundle):
                transducer.add_arc(Arc(state, segment, NULL_SEGMENT, CostVector.get_vector(1, 1), state))
            else:
                transducer.add_arc(Arc(state, segment, NULL_SEGMENT, CostVector.get_vector(1, 0), state))

        if get_configuration("ALLOW_CANDIDATES_WITH_CHANGED_SEGMENTS"):
            for first_segment, second_segment in permutations(segments, 2):
                transducer.add_arc(Arc(state, first_segment, second_segment, CostVector.get_vector(1, 0), state))

        return transducer

    @classmethod
    def get_constraint_name(cls):
        return "Max"


class DepConstraint(Constraint):
    def __init__(self, bundles_list):
        super(DepConstraint, self).__init__(bundles_list, False)
        self.feature_bundle = self.feature_bundles[0]

    def _make_transducer(self):
        transducer, segments, state = super(DepConstraint, self)._base_faithfulness_transducer()
        for segment in segments:
            transducer.add_arc(Arc(state, segment, segment, CostVector.get_vector(1, 0), state))
            transducer.add_arc(Arc(state, segment, NULL_SEGMENT, CostVector.get_vector(1, 0), state))
            if segment.has_feature_bundle(self.feature_bundle):
                transducer.add_arc(Arc(state, NULL_SEGMENT, segment, CostVector.get_vector(1, 1), state))
            else:
                transducer.add_arc(Arc(state, NULL_SEGMENT, segment, CostVector.get_vector(1, 0), state))

        if get_configuration("ALLOW_CANDIDATES_WITH_CHANGED_SEGMENTS"):
            for first_segment, second_segment in permutations(segments, 2):
                transducer.add_arc(Arc(state, first_segment, second_segment, CostVector.get_vector(1, 0), state))

        return transducer

    @classmethod
    def get_constraint_name(cls):
        return "Dep"


class IdentConstraint(Constraint):
    def __init__(self, bundles_list):
        super(IdentConstraint, self).__init__(bundles_list, False)
        self.feature_bundle = self.feature_bundles[0]

    def _make_transducer(self):
        transducer, segments, state = super(IdentConstraint, self)._base_faithfulness_transducer()
        for segment in segments:
            transducer.add_arc(Arc(state, segment, segment, CostVector.get_vector(1, 0), state))
            transducer.add_arc(Arc(state, segment, NULL_SEGMENT, CostVector.get_vector(1, 0), state))
            transducer.add_arc(Arc(state, NULL_SEGMENT, segment, CostVector.get_vector(1, 0), state))
            input_segment = segment
            if input_segment.has_feature_bundle(self.feature_bundle):
                for output_segment in segments:
                    if output_segment.has_feature_bundle(self.feature_bundle):
                        transducer.add_arc(Arc(state, input_segment, output_segment, CostVector.get_vector(1, 0), state))
                    else:
                        transducer.add_arc(Arc(state, input_segment, output_segment, CostVector.get_vector(1, 1), state))
            else:
                for output_segment in segments:
                    transducer.add_arc(Arc(state, input_segment, output_segment, CostVector.get_vector(1, 0), state))
        return transducer

    @classmethod
    def get_constraint_name(cls):
        return "Ident"


class FaithConstraint(Constraint):
    """This constraint has no feature bundle list"""
    def __init__(self, bundles_list):
        super(FaithConstraint, self).__init__([], False)

    def _make_transducer(self):
        transducer, segments, state = super(FaithConstraint, self)._base_faithfulness_transducer()
        for segment in segments:
            transducer.add_arc(Arc(state, NULL_SEGMENT, segment, CostVector.get_vector(1, 1), state))
            transducer.add_arc(Arc(state, segment, NULL_SEGMENT, CostVector.get_vector(1, 1), state))
            transducer.add_arc(Arc(state, segment, segment, CostVector.get_vector(1, 0), state))

        if get_configuration("ALLOW_CANDIDATES_WITH_CHANGED_SEGMENTS"):
            for first_segment, second_segment in permutations(segments, 2):
                transducer.add_arc(Arc(state, first_segment, second_segment, CostVector.get_vector(1, 1), state))

        return transducer


    @classmethod
    def get_constraint_name(cls):
        return "Faith"


class PhonotacticConstraint(Constraint):
    def __init__(self, bundles_list):
        super(PhonotacticConstraint, self).__init__(bundles_list, True)

    def insert_feature_bundle(self):
        if len(self.feature_bundles) < get_configuration("MAX_FEATURE_BUNDLES_IN_PHONOTACTIC_CONSTRAINT"):
            new_feature_bundle = FeatureBundle.generate_random()
            self.feature_bundles.insert(randint(0, len(self.feature_bundles)), new_feature_bundle)
            return True
        else:
            return False

    def remove_feature_bundle(self):
        if len(self.feature_bundles) > get_configuration("MIN_FEATURE_BUNDLES_IN_PHONOTACTIC_CONSTRAINT"):
            self.feature_bundles.pop(randint(0, len(self.feature_bundles)-1))

            return True
        else:
            return False

    def _make_transducer(self):
        def compute_num_of_max_satisfied_bundle(segment):
            i = 0
            while i < n and symbol_bundle_characteristic_matrix[segment][i]:
                i += 1
            return i

        def compute_highest_num_of_satisfied_bundle(segment, j):
            for k in range(j + 1, 0, -1):
                if symbol_bundle_characteristic_matrix[segment][k-1]:
                    return k
            else:
                return 0

        n = len(self.feature_bundles) - 1
        segments = self.feature_table.get_segments()
        transducer = Transducer(segments, name=str(self))

        symbol_bundle_characteristic_matrix = {segment: [segment.has_feature_bundle(self.feature_bundles[i])
                                                         for i in range(n+1)]
                                               for segment in segments}

        states = {i: {j: 0 for j in range(i)} for i in range(n+1)}

        initial_state = State('q0|0')    # here we use a tuple as label. it will change at the end of this function
        states[0][0] = initial_state

        transducer.set_as_single_state(initial_state)

        if not n:
            for segment in segments:
                transducer.add_arc(Arc(states[0][0], JOKER_SEGMENT, segment, CostVector([int(symbol_bundle_characteristic_matrix[segment][0])]), states[0][0]))
            transducer.add_arc(Arc(states[0][0], JOKER_SEGMENT, NULL_SEGMENT, CostVector([0]), states[0][0]))

        else:
            for i in range(0, n+1):
                for j in range(i):
                    state = State('q{0}|{1}'.format(i,j))
                    states[i][j] = state
                    transducer.add_state(state)
            max_num_of_satisfied_bundle_by_segment = {segment: compute_num_of_max_satisfied_bundle(segment)
                                                      for segment in segments}
            for segment in segments:
                transducer.add_arc(Arc(states[0][0], JOKER_SEGMENT, segment, CostVector([0]),
                                       states[symbol_bundle_characteristic_matrix[segment][0]][0]))
            for i in range(n+1):
                for j in range(i):
                    state = states[i][j]
                    transducer.add_final_state(state)
                    if i != n:
                        for segment in segments:
                            if symbol_bundle_characteristic_matrix[segment][i]:
                                new_state_level = i+1
                                new_state_mem = min([j+1, max_num_of_satisfied_bundle_by_segment[segment]])
                            else:
                                new_state_level = compute_highest_num_of_satisfied_bundle(segment, j)
                                new_state_mem = min([max_num_of_satisfied_bundle_by_segment[segment],
                                                     abs(new_state_level - 1)])
                            new_terminus = states[new_state_level][new_state_mem]
                            transducer.add_arc(Arc(state, JOKER_SEGMENT, segment, CostVector([0]), new_terminus))

                    else:  # i = n
                        for segment in segments:
                            new_state_level = compute_highest_num_of_satisfied_bundle(segment, j)
                            new_state_mem = min([max_num_of_satisfied_bundle_by_segment[segment],
                                                 abs(new_state_level - 1)])
                            new_terminus = states[new_state_level][new_state_mem]
                            transducer.add_arc(Arc(state, JOKER_SEGMENT, segment,
                                                   CostVector([int(symbol_bundle_characteristic_matrix[segment][i])]), new_terminus))

        transducer.clear_dead_states()
        for state in transducer.states:
            transducer.add_arc(Arc( state, JOKER_SEGMENT, NULL_SEGMENT, CostVector([0]), state))
        return transducer

    @classmethod
    def get_constraint_name(cls):
        return "Phonotactic"



    def get_encoding_length(self):
        return 1 + sum([featureBundle.get_encoding_length() for featureBundle in self.feature_bundles]) \
                 + len(self.feature_bundles) + 1

    @classmethod
    def generate_random(cls):
        bundles = list()
        for i in range(get_configuration("INITIAL_NUMBER_OF_BUNDLES_IN_PHONOTACTIC_CONSTRAINT")):
            bundles.append(FeatureBundle.generate_random())
        return PhonotacticConstraint(bundles)


class VowelHarmonyConstraint(Constraint): #for Tuvan VH test
    def __init__(self, bundles_list):
        super(VowelHarmonyConstraint, self).__init__(bundles_list, True)

    def insert_feature_bundle(self):
        if len(self.feature_bundles) < get_configuration("MAX_FEATURE_BUNDLES_IN_PHONOTACTIC_CONSTRAINT"):
            new_feature_bundle = FeatureBundle.generate_random()
            self.feature_bundles.insert(randint(0, len(self.feature_bundles)), new_feature_bundle)
            return True
        else:
            return False

    def remove_feature_bundle(self):
        if len(self.feature_bundles) > get_configuration("MIN_FEATURE_BUNDLES_IN_PHONOTACTIC_CONSTRAINT"):
            self.feature_bundles.pop(randint(0, len(self.feature_bundles)-1))

            return True
        else:
            return False

    def _make_transducer(self):
        def compute_num_of_max_satisfied_bundle(segment):
            i = 0
            while i < n and symbol_bundle_characteristic_matrix[segment][i]:
                i += 1
            return i

        def compute_highest_num_of_satisfied_bundle(segment, j):
            for k in range(j + 1, 0, -1):
                if symbol_bundle_characteristic_matrix[segment][k-1]:
                    return k
            else:
                return 0

        n = len(self.feature_bundles) - 1
        segments = self.feature_table.get_segments()
        transducer = Transducer(segments, name=str(self))

        symbol_bundle_characteristic_matrix = {segment: [segment.has_feature_bundle(self.feature_bundles[i])
                                                         for i in range(n+1)]
                                               for segment in segments}

        states = {i: {j: 0 for j in range(i)} for i in range(n+1)}

        initial_state = State('q0|0')    # here we use a tuple as label. it will change at the end of this function
        states[0][0] = initial_state

        transducer.set_as_single_state(initial_state)

        if not n:
            for segment in segments:
                transducer.add_arc(Arc(states[0][0], JOKER_SEGMENT, segment, CostVector([int(symbol_bundle_characteristic_matrix[segment][0])]), states[0][0]))
            transducer.add_arc(Arc(states[0][0], JOKER_SEGMENT, NULL_SEGMENT, CostVector([0]), states[0][0]))

        else:
            for i in range(0, n+1):
                for j in range(i):
                    state = State('q{0}|{1}'.format(i,j))
                    states[i][j] = state
                    transducer.add_state(state)
            max_num_of_satisfied_bundle_by_segment = {segment: compute_num_of_max_satisfied_bundle(segment)
                                                      for segment in segments}
            for segment in segments:
                transducer.add_arc(Arc(states[0][0], JOKER_SEGMENT, segment, CostVector([0]),
                                       states[symbol_bundle_characteristic_matrix[segment][0]][0]))
            for i in range(n+1):
                for j in range(i):
                    state = states[i][j]
                    transducer.add_final_state(state)
                    if i != n:
                        for segment in segments:
                            if symbol_bundle_characteristic_matrix[segment][i]:
                                new_state_level = i+1
                                new_state_mem = min([j+1, max_num_of_satisfied_bundle_by_segment[segment]])
                            else:
                                new_state_level = compute_highest_num_of_satisfied_bundle(segment, j)
                                new_state_mem = min([max_num_of_satisfied_bundle_by_segment[segment],
                                                     abs(new_state_level - 1)])
                            new_terminus = states[new_state_level][new_state_mem]
                            transducer.add_arc(Arc(state, JOKER_SEGMENT, segment, CostVector([0]), new_terminus))
                            transducer.add_arc(Arc(new_terminus, JOKER_SEGMENT, segment, CostVector([0]), new_terminus))
                    else:  # i = n
                        for segment in segments:
                            new_state_level = compute_highest_num_of_satisfied_bundle(segment, j)
                            new_state_mem = min([max_num_of_satisfied_bundle_by_segment[segment],
                                                 abs(new_state_level - 1)])
                            new_terminus = states[new_state_level][new_state_mem]
                            transducer.add_arc(Arc(state, JOKER_SEGMENT, segment,
                                                   CostVector([int(symbol_bundle_characteristic_matrix[segment][i])]), new_terminus))

        transducer.clear_dead_states()
        for state in transducer.states:
            transducer.add_arc(Arc( state, JOKER_SEGMENT, NULL_SEGMENT, CostVector([0]), state))
        return transducer

    @classmethod
    def get_constraint_name(cls):
        return "VowelHarmony"
