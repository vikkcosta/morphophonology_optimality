from random import choice, randint
from collections import namedtuple
from copy import deepcopy
from io import StringIO
from utils import get_configuration, get_feature_table, get_weighted_list, ceiling_of_log_two
from FAdo.fa import NFA, Epsilon
from debug_tools import write_to_dot
from typing import Dict, List

INITIAL_STATE = 'q0'
FINAL_STATE = 'qf'
q1 = 'q1'
q2 = 'q2'
q3 = 'q3'


StateTuple = namedtuple('StateTuple', ['start_state', 'end_state'])


class HMM:
    def __init__(self, transitions, emissions, inner_states):
        self.feature_table = get_feature_table()
        self.transitions: Dict = transitions
        self.emissions: Dict = emissions
        self.inner_states: List = inner_states
        self.nfa = self._get_nfa()

    @classmethod
    def create_hmm_from_list(cls, word_string_list):
        transition_dict = {INITIAL_STATE: [q1], q1: [FINAL_STATE]}
        emission_dict = {q1: word_string_list}
        transitions = {k: v for k, v in transition_dict.items()}
        emissions = {k: v for k, v in emission_dict.items()}
        inner_states = [q1]
        hmm = HMM(transitions, emissions, inner_states)
        return hmm

    @classmethod
    def create_hmm_alphabet(cls, alphabet):
        transition_dict = {INITIAL_STATE: [q1], q1: [q1, FINAL_STATE]}
        emission_dict = {q1: alphabet}
        transitions = {k: v for k, v in transition_dict.items()}
        emissions = {k: v for k, v in emission_dict.items()}
        inner_states = [q1]
        hmm = HMM(transitions, emissions, inner_states)
        return hmm

    def make_mutation(self):
        mutation_weights = [
            (self.advance_emission, get_configuration("ADVANCE_EMISSION")),
            (self.clone_state, get_configuration("CLONE_STATE")),
            (self.clone_emission, get_configuration("CLONE_EMISSION")),
            (self.add_segment_to_emission, get_configuration("ADD_SEGMENT_TO_EMISSION")),
            (self.remove_segment_from_emission, get_configuration("REMOVE_SEGMENT_FROM_EMISSION")),
            (self.change_segment_in_emission,  get_configuration("CHANGE_SEGMENT_IN_EMISSION")),
            (self.add_state, get_configuration("ADD_STATE")),
            (self.remove_state, get_configuration("REMOVE_STATE")),
            (self.add_transition, get_configuration("ADD_TRANSITION")),
            (self.remove_transition, get_configuration("REMOVE_TRANSITION")),
            (self.add_emission_to_state, get_configuration("ADD_EMISSION_TO_STATE")),
            (self.remove_emission_from_state, get_configuration("REMOVE_EMISSION_FROM_STATE")),
        ]

        weighted_mutations_list = get_weighted_list(mutation_weights)
        chosen_mutation = choice(weighted_mutations_list)
        mutation_result = chosen_mutation()
        if mutation_result:
            self.nfa = self._get_nfa()
        return mutation_result

    def advance_emission(self):
        target_state = choice(self.inner_states)
        target_state_emissions = self.get_emissions(target_state)
        if target_state in self.transitions[target_state] and len(self.transitions[target_state]) > 1\
                and len(target_state_emissions) > 1 and len(self.inner_states) < get_configuration("MAX_NUM_OF_INNER_STATES"):
            #check if there is a loop and another outgoing state
            outgoing_states_list = list(set(self.transitions[target_state]) - set([target_state]))
            outgoing_state = choice(outgoing_states_list)
            new_state = self._get_next_state()
            emission = choice(target_state_emissions)

            self.inner_states.append(new_state)
            self.transitions[new_state] = [outgoing_state, new_state, target_state]
            self.emissions[new_state] = [emission]

            self.transitions[target_state].append(new_state)
            self.emissions[target_state].remove(emission)
            return True
        else:
            return False

    def clone_state(self):
        """pick an inner state, create a new state with same transitions and emissions,
         if the original state a transition to itself the original and the new will be connected"""
        if len(self.inner_states) < get_configuration("MAX_NUM_OF_INNER_STATES"):
            original_state = choice(self.inner_states)
            cloned_state = self._get_next_state()
            self.inner_states.append(cloned_state)
            self.emissions[cloned_state] = deepcopy(self.emissions[original_state])

            #create incoming connections
            for state in self.transitions:
                if original_state in self.transitions[state]:
                    self.transitions[state].append(cloned_state)

            #copy outgoing connections
            self.transitions[cloned_state] = deepcopy(self.transitions[original_state])
            import time

            #write_to_dot(self, "runtime_hmm_{}".format(get_global_datum("step")))
            return True
        else:
            return False

    def clone_emission(self):
        """pick an emission
           pick an inner state and add the emission to it"""
        emissions = self.get_all_emissions()
        emission = choice(emissions)
        state = choice(self.inner_states)
        if emission not in self.get_emissions(state):
            self.emissions[state].append(emission)
            return True
        else:
            return False

    def add_state(self):
        """adds empty state"""
        if len(self.inner_states) < get_configuration("MAX_NUM_OF_INNER_STATES"):
            new_state = self._get_next_state()
            self.inner_states.append(new_state)
            self.emissions[new_state] = []
            self.transitions[new_state] = []
            return True
        else:
            return False

    def remove_state(self):
        """removes an inner state (and all it's arcs)"""
        if len(self.inner_states) > get_configuration("MIN_NUM_OF_INNER_STATES"):
            state_to_remove = choice(self.inner_states)
            self.inner_states.remove(state_to_remove)
            del self.emissions[state_to_remove]
            del self.transitions[state_to_remove]

            for state in self.transitions:
                if state_to_remove in self.transitions[state]:
                    self.transitions[state].remove(state_to_remove)
            return True
        else:
            return False

    def add_transition(self):
        """picks a state form initial+inner states and add transition
        to other random state (in case initial, not to itself)"""
        state1 = choice(self.inner_states + [INITIAL_STATE])
        state2 = choice(self.inner_states)
        if state2 not in self.get_transitions(state1):
            self.transitions[state1].append(state2)
            return True
        else:
            return False

    def remove_transition(self):
        """picks a state form initial+inner states and remove a transition from it"""
        state1 = choice(self.inner_states + [INITIAL_STATE])
        if not len(self.get_transitions(state1)):
            return False
        else:
            state2 = choice(self.get_transitions(state1))
            self.transitions[state1].remove(state2)
            return True

    def add_emission_to_state(self):
        """pick an inner state, pick a segment - add segment to state """
        state = choice(self.inner_states)
        feature_table = get_feature_table()
        segment = feature_table.get_random_segment()
        if segment not in self.get_emissions(state):
            self.emissions[state].append(segment)
            return True
        else:
            return False

    def remove_emission_from_state(self):
        """pick an inner state, pick an emission - remove it (if state has no emissions - mutation failed)"""
        state = choice(self.inner_states)
        emissions = self.get_emissions(state)
        if emissions:
            emission = choice(emissions)
            self.emissions[state].remove(emission)
            return True
        else:
            return False

    def add_segment_to_emission(self):
        """pick an inner state, pick an emission, pick a segment and insert in random position"""

        state = choice(self.inner_states)
        if self.get_emissions(state):
            original_emission = choice(self.get_emissions(state))
            feature_table = get_feature_table()
            segment_to_insert = feature_table.get_random_segment()

            insertion_index = randint(0, len(original_emission))
            new_emission = original_emission[:insertion_index] + segment_to_insert + original_emission[insertion_index:]
            if new_emission not in self.get_emissions(state):
                self.emissions[state].append(new_emission)
                return True
        return False

    def remove_segment_from_emission(self):
        """pick an inner state, pick an emission, pick a position and remove from it -
        if the emission is mono-segmental, remove it"""

        state = choice(self.inner_states)
        emissions = self.get_emissions(state)
        if emissions:
            emission = choice(emissions)
            if not len(emission) == 1:
                deletion_index = randint(0, len(emission) - 1)
                new_emission = emission[:deletion_index] + emission[deletion_index + 1:]
                if new_emission not in self.get_emissions(state):
                    self.emissions[state].append(new_emission)

            return True
        return False

    def change_segment_in_emission(self):
        """pick a state, pick an emission, pick a segment, change it"""
        state = choice(self.inner_states)
        emissions = self.get_emissions(state)
        if emissions:
            emission = choice(emissions)
            # crate new emission
            emission_string_list = list(emission)
            index_of_change = randint(0, len(emission_string_list) - 1)
            old_segment = emission_string_list[index_of_change]
            feature_table = get_feature_table()
            segments = feature_table.get_alphabet()
            segments.remove(old_segment)
            new_segment = choice(segments)
            emission_string_list[index_of_change] = new_segment
            new_emission = ''.join(emission_string_list)

            # replace emission
            emissions.append(new_emission)
            return True
        else:
            return False

    def get_emissions(self, state):
        return self.emissions.get(state, [])

    def get_encoding_length(self):
        encoding_length = 0
        state_symbols_in_transitions = 0
        total_num_of_emissions = 0
        segments_in_emissions = 0

        states_list = self.get_states()
        for state in states_list:
                state_symbols_in_transitions += len(self.get_transitions(state)) + 1  # +1 indicate the origin state

                for emission in self.get_emissions(state):
                    total_num_of_emissions += 1
                    segments_in_emissions += len(emission)

        segment_symbol_length = ceiling_of_log_two(len(self.feature_table) + 1)
        states_symbol_length = ceiling_of_log_two(len(states_list) + 1)

        num_bits = states_symbol_length + 1
        content_usage = (state_symbols_in_transitions * states_symbol_length) + (segments_in_emissions * segment_symbol_length)
        delimiter_usage = (len(states_list) * segment_symbol_length) + \
                          (len(states_list) * states_symbol_length) +  \
                          total_num_of_emissions * segment_symbol_length
        encoding_length += num_bits + content_usage + delimiter_usage

        return encoding_length


    def get_all_emissions(self):
        emissions = set()
        for state in self.emissions:
            emissions |= set(self.emissions[state])
        return list(emissions)

    def get_states(self):
        return [INITIAL_STATE] + self.inner_states + [FINAL_STATE]

    def _get_next_state(self):
        state_numbers = [int(x[1:]) for x in self.inner_states]  # remove 'q'
        state_numbers.append(0)
        state_numbers.sort()
        next_state_number = None

        if len(state_numbers) == state_numbers[-1] + 1:
            next_state_number = len(state_numbers)
        else:
            for i in range(len(state_numbers) - 1):
                if state_numbers[i] + 1 != state_numbers[i + 1]:
                    next_state_number = i + 1
                    break

        new_state = 'q{}'.format(next_state_number)

        return new_state

    def get_transitions(self, state):
        """used in get_encoding_length"""
        return self.transitions.get(state, [])

    def get_string_words_up_to_length(self, max_length):
        string_words = self.nfa.enumNFA(max_length)
        string_words.remove("")
        return string_words

    def _get_nfa(self):
        list_of_nfa_states = []
        NFA_INITIAL_STATE = INITIAL_STATE
        NFA_FINAL_STATE = FINAL_STATE
        nfa = NFA()
        list_of_nfa_states.append(NFA_INITIAL_STATE)
        list_of_nfa_states.append(NFA_FINAL_STATE)

        # create  states
        state_dict = dict()
        state_dict[NFA_INITIAL_STATE] = StateTuple(None, NFA_INITIAL_STATE)
        for hmm_state in sorted(self.inner_states):  # sorted for consistency in encoding later on
            start_state = "{}_start".format(hmm_state)
            end_state = "{}_end".format(hmm_state)
            list_of_nfa_states.extend([start_state, end_state])
            state_dict[hmm_state] = StateTuple(start_state, end_state)  # state_dict["q1(hmm)]" =
            # ("q1_start(nfa)", "q1_end

        # create emission states
        for hmm_state in self.emissions:
            for emission_index, emission in enumerate(self.emissions[hmm_state]):
                emission_states_list = ["{},{},{}".format(hmm_state, emission_index, segment_index)
                                        for segment_index in range(len(emission) - 1)]
                list_of_nfa_states.extend(emission_states_list)

        state_to_state_index = {}
        for state in list_of_nfa_states:
            state_index = nfa.addState(state)
            state_to_state_index[state] = state_index

        nfa.setInitial([state_to_state_index[NFA_INITIAL_STATE]])
        nfa.setFinal([state_to_state_index[NFA_FINAL_STATE]])

        # transitןon arcs
        for hmm_state1 in self.transitions:
            for hmm_state2 in self.transitions[hmm_state1]:
                state1 = state_dict[hmm_state1].end_state
                state1_index = state_to_state_index[state1]
                if hmm_state2 != NFA_FINAL_STATE:
                    state2 = state_dict[hmm_state2].start_state
                    state2_index = state_to_state_index[state2]
                    nfa.addTransition(state1_index, Epsilon, state2_index)
                else:
                    final_state_index = state_to_state_index[NFA_FINAL_STATE]
                    nfa.addTransition(state1_index, Epsilon, final_state_index)

        # emission arcs
        for hmm_state in self.emissions:
            start_state = state_dict[hmm_state].start_state
            end_state = state_dict[hmm_state].end_state
            for emission_index, emission in enumerate(self.emissions[hmm_state]):
                string_states_list = [start_state] + ["{},{},{}".format(hmm_state, emission_index, segment_index)
                                                      for segment_index in range(len(emission) - 1)] + [end_state]
                states_index_list = [state_to_state_index[state] for state in string_states_list]

                for i in range(len(emission)):
                    nfa.addTransition(states_index_list[i], emission[i], states_index_list[i + 1])
        #dot(nfa, "hmm_nfa")
        return nfa

    def get_log_lines(self):
        log_lines = list()
        log_lines.append("HMM:")
        log_lines.append("{}: {}".format(INITIAL_STATE, sorted(self.transitions[INITIAL_STATE])))

        for state in sorted(self.inner_states):
            emissions = sorted(self.emissions[state])
            transitions = sorted(self.transitions[state])
            log_lines.append("{}: {}, {}".format(state, sorted(transitions), sorted(emissions)))


        for path in self.get_all_paths():
            log_lines.append("->".join(path))
        #log_lines.append("All Emissions: {}".format(sorted(self.get_all_emissions())))

        return log_lines

    def get_all_paths(self):
        paths = []
        stack = [(INITIAL_STATE, [INITIAL_STATE])]
        while stack:
            (vertex, path) = stack.pop()
            for next in set(self.transitions[vertex]) - set(path):
                if next == FINAL_STATE:
                    paths.append(path + [next])
                else:
                    stack.append((next, path + [next]))
        return paths


    def draw(self):
        def weight_str(dict_, key, value):
            weight = 1
            if weight != 1:
                return "({})".format(weight)
            else:
                return ""

        str_io = StringIO()
        print("digraph acceptor {", file=str_io, end="\n")
        print("rankdir=LR", file=str_io, end="\n")
        print("size=\"11,5\"", file=str_io, end="\n")
        print("node [shape = ellipse];", file=str_io, end="\n")

        print("//transitions arcs", file=str_io, end="\n")
        for state1 in self.transitions:
            for state2 in self.transitions[state1]:
                print("\"{}\" ->  \"{}\" [label=\"{}\"];".format(state1, state2,
                                                                 weight_str(self.transitions, state1, state2)),
                      file=str_io, end="\n")

        print("//emission tables lines", file=str_io, end="\n")
        for state in self.emissions:
            print("\"{}\" -- {}_emission_table".format(state, state), file=str_io, end="\n")

        print("//emission tables", file=str_io, end="\n")
        for state in self.inner_states:
            emissions_label = ""
            for emission in self.emissions[state]:
                emissions_label += "{} {}\\n".format(emission, weight_str(self.emissions, state, emission))
            print("{}_emission_table [shape=none, label=\"{}\"]".format(state, emissions_label), file=str_io, end="\n")

        print("\"q0\" [style=filled];", file=str_io, end="\n")
        print("\"qf\" [peripheries=2];", file=str_io, end="\n")
        print("}", file=str_io, end="")

        return str_io.getvalue()
