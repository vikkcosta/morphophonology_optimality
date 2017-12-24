from math import log
from copy import deepcopy
from io import StringIO
from utils import ceiling_of_log_two
from typing import Dict, Set
from FAdo.fa import Epsilon as fado_epsilon

NULL_SEGMENT = "-"


class TableCell:
    def __init__(self, probability, output, state_back_pointer, position_back_pointer):
        self.probability = probability
        self.output = output
        self.state_back_pointer = state_back_pointer
        self.position_back_pointer = position_back_pointer

    def __repr__(self):
        return "{:.2f}, ({}, {})".format(self.probability, self.state_back_pointer, self.position_back_pointer)


class ParsingNFA:
    """
    this implementation it not aimed to allow flexible changes to the nfa,
    the nfa is converted from a fado NFA for order of quick parsing
    """
    def __init__(self):
        self.initial_state = None
        self.final_states = None
        self.arcs_dict = None

    @classmethod
    def get_from_fado_nfa(cls, fado_nfa):
        parsing_nfa = ParsingNFA()
        parsing_nfa.final_states = list()
        parsing_nfa.initial_state = fado_nfa.States[list(fado_nfa.Initial)[0]]
        parsing_nfa.final_states.append(fado_nfa.States[list(fado_nfa.Final)[0]])

        fado_nfa_states = fado_nfa.States
        fado_nfa_arc_dict: Dict[int, Dict[str, Set[int]]] = fado_nfa.delta

        parsing_nfa_arcs_dict: Dict[str, Dict[str, list[str]]] = dict()

        for fado_origin_state_index in fado_nfa_arc_dict:
            parsing_nfa_origin_state = fado_nfa_states[fado_origin_state_index]
            if parsing_nfa_origin_state not in parsing_nfa_arcs_dict:
                parsing_nfa_arcs_dict[parsing_nfa_origin_state]: Dict[str, list[str]] = dict()

            for fado_output_symbol in fado_nfa_arc_dict[fado_origin_state_index]:
                if fado_output_symbol == fado_epsilon:
                    parsing_nfa_output_symbol = NULL_SEGMENT
                else:
                    parsing_nfa_output_symbol = fado_output_symbol
                if parsing_nfa_output_symbol not in parsing_nfa_arcs_dict[parsing_nfa_origin_state]:
                    parsing_nfa_arcs_dict[parsing_nfa_origin_state][parsing_nfa_output_symbol] = list()

                for terminal_state_index in fado_nfa_arc_dict[fado_origin_state_index][fado_output_symbol]:
                    parsing_nfa_terminal_state = fado_nfa_states[terminal_state_index]
                    parsing_nfa_arcs_dict[parsing_nfa_origin_state][parsing_nfa_output_symbol].append(parsing_nfa_terminal_state)

        parsing_nfa.arcs_dict = parsing_nfa_arcs_dict
        return parsing_nfa

    def parse(self, observation):  # used by: hypothesis
        observation = " " + observation + " "
        observation_length = len(observation)
        table = [{} for _ in range(observation_length)]

        # Initialize the first column
        for segment in self.arcs_dict.get(self.initial_state, []):
            for state2 in self.arcs_dict[self.initial_state][segment]:
                probability = self._get_probability(self.initial_state)
                table_cell = TableCell(log(probability), segment, self.initial_state, 0)
                if probability:
                    if segment is NULL_SEGMENT:
                        table[0][state2] = table_cell
                    elif segment == observation[1]:
                        table[1][state2] = table_cell

        # fill out the rest of the table
        for position in range(1, observation_length):
            states = deepcopy(table[position - 1])
            while states:
                new_states = set()
                for state1 in states:
                    if state1 in self.final_states:
                        continue
                    for segment in self.arcs_dict.get(state1, []):
                        for state2 in self.arcs_dict[state1][segment]:
                            probability = self._get_probability(state1)
                            if probability:
                                combined_probability = log(probability) + table[position - 1][state1].probability
                                table_cell = TableCell(combined_probability, segment, state1, position - 1)
                                if segment is NULL_SEGMENT:
                                    if state2 not in table[position - 1]:
                                        table[position - 1][state2] = table_cell
                                        new_states.add(state2)
                                    elif combined_probability > table[position - 1][state2].probability:
                                        table[position - 1][state2] = table_cell
                                        new_states.add(state2)
                                elif segment == observation[position]:
                                    if state2 not in table[position]:
                                        table[position][state2] = table_cell
                                    elif combined_probability > table[position][state2].probability:
                                        table[position][state2] = table_cell
                states = new_states

        optimal_final_state = None
        optimal_probability = float("-inf")
        for final_state in self.final_states:
            if final_state in table[-2]:
                probability = table[-2][final_state].probability
                if probability > optimal_probability:
                    optimal_final_state = final_state
                    optimal_probability = probability

        if not optimal_final_state:
            return None

        current_state = optimal_final_state
        current_position = len(table) - 2
        backward_states_path = [current_state]
        backward_outputs_path = list()
        while True:
            current_cell = table[current_position][current_state]
            current_state = current_cell.state_back_pointer
            current_position = current_cell.position_back_pointer
            current_output = current_cell.output
            backward_states_path.append(current_state)
            backward_outputs_path.append(current_output)
            if current_state == self.initial_state:
                break

        states_path = list(reversed(backward_states_path))
        outputs_path = list(reversed(backward_outputs_path))
        #exit(0)
        return states_path, outputs_path

    def get_parse_encoding_length(self, parse):
        encoding_length = 0
        states_path = parse[0]
        for state in states_path[:-1]:
            bits_for_transition = ceiling_of_log_two(self._get_number_of_outgoing_states(state))
            encoding_length += bits_for_transition
        return encoding_length

    def get_observation_encoding_length(self, observation):
        parse = self.parse(observation)
        encoding_length = self.get_parse_encoding_length(parse)
        return encoding_length

    def _get_number_of_outgoing_states(self, state):
        states = set()
        for segment in self.arcs_dict[state]:
            for outgoing_state in self.arcs_dict[state][segment]:
                states.add(outgoing_state)
        return len(states)

    def _get_probability(self, state):
        return 1/self._get_number_of_outgoing_states(state)

    def draw(self):
        str_io = StringIO()
        print("digraph acceptor {", file=str_io, end="\n")
        print("rankdir=LR", file=str_io, end="\n")
        print("size=\"11,5\"", file=str_io, end="\n")
        print("node [shape = ellipse];", file=str_io, end="\n")

        print("// arcs: source -> dest [label]", file=str_io, end="\n")
        print(self._arcs_dot_representation(), file=str_io, end="")

        print("// start nodes", file=str_io, end="\n")
        print("\"{}\" [style=filled];".format(self.initial_state), file=str_io, end="\n")

        print("// final nodes", file=str_io, end="\n")
        for state in self.final_states:
            print("\"{}\" [peripheries=2];".format(state), file=str_io, end="\n")

        print("}", file=str_io, end="")

        return str_io.getvalue()

    def _arcs_dot_representation(self):  # used by draw
        str_io = StringIO()
        printed_multiple_arcs = list()
        segment_by_state_dict = self._get_segment_by_state_dict()
        for origin_state in self.arcs_dict:

            print(origin_state)
            print(self.arcs_dict[origin_state].values())
            terminal_state_list = [item for sublist in self.arcs_dict[origin_state].values() for item in sublist]
            #nightmare in c++

            for terminal_state in terminal_state_list:
                if len(segment_by_state_dict[origin_state][terminal_state]) > 1:
                   if (origin_state, terminal_state) not in printed_multiple_arcs:
                       combined_label = ""
                       segments = segment_by_state_dict[origin_state][terminal_state]
                       for segment in segments:
                           combined_label += "{} \\n".format(segment)

                       combined_label += "\\n" * len(segments)

                       print("\"{}\" -> \"{}\" [label=\"{}\"];".format(
                         origin_state, terminal_state, combined_label), file=str_io, end="\n")
                       printed_multiple_arcs.append((origin_state, terminal_state))

                else:
                    segment = next(iter(segment_by_state_dict[origin_state][terminal_state])) # get the single element from set
                    print("\"{}\" -> \"{}\" [label=\"{} \\n\"];".format(
                    origin_state, terminal_state, segment), file=str_io, end="\n")

        arcs_dot_representation = str_io.getvalue()
        return arcs_dot_representation

    def _get_segment_by_state_dict(self):  # used by _arcs_dot_representation
        segment_by_state_dict = dict()
        for origin_state in self.arcs_dict:
            for segment_terminal_state_list_tuple in self.arcs_dict[origin_state].items():
                segment = segment_terminal_state_list_tuple[0]
                terminal_state_list = segment_terminal_state_list_tuple[1]
                for terminal_state in terminal_state_list:
                    if origin_state not in segment_by_state_dict:
                        segment_by_state_dict[origin_state] = dict()
                    if terminal_state not in segment_by_state_dict[origin_state]:
                        segment_by_state_dict[origin_state][terminal_state] = [segment]
                    else:  # after else - not tested
                        for i, existing_tuple in enumerate(segment_by_state_dict[origin_state][terminal_state]):
                            if existing_tuple == segment:
                                segment_by_state_dict[origin_state][terminal_state][i] = segment
                                break
                        else:
                            segment_by_state_dict[origin_state][terminal_state].append(segment)
        #print(segment_by_state_dict)
        return segment_by_state_dict

    def __str__(self):
        str_io = StringIO()
        print("initial state: {0}".format(self.initial_state), file=str_io, end="\n")
        print("final states: {0}".format(self.final_states), file=str_io, end="\n")
        print("arcs_dict: {0}".format(self.arcs_dict), file=str_io, end="\n")
        return str_io.getvalue()
