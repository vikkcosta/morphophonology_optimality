import json
import logging
from copy import deepcopy
from io import StringIO
from os.path import splitext
from random import choice
from singelton import Singleton

logger = logging.getLogger(__name__)


class FeatureTable(metaclass=Singleton):
    def __init__(self, feature_table_dict_from_json):
        self.feature_table_dict = dict()
        self.feature_types_dict = dict()
        self.segments_list = list()
        feature_type_list = [dict(**feature) for feature in feature_table_dict_from_json['feature']]
        feature_types_label_in_order = [feature['label'] for feature in feature_table_dict_from_json['feature']]

        for feature_type_label in feature_types_label_in_order:
            if feature_types_label_in_order.count(feature_type_label) > 1:
                raise ValueError('feature "{}" appears more then one time'.format(feature_type_label))

        self.feature_order_dict = dict()
        for i, feature in enumerate(feature_types_label_in_order):
            self.feature_order_dict[i] = feature

        for feature_type in feature_type_list:
            self.feature_types_dict[feature_type['label']] = feature_type['values']

        for symbol in feature_table_dict_from_json['feature_table'].keys():
            feature_values = feature_table_dict_from_json['feature_table'][symbol]
            if len(feature_values) != len(self.feature_types_dict):
                raise ValueError("Mismatch in number of features for segment {0}".format(symbol))
            symbol_feature_dict = dict()
            for i, feature_value in enumerate(feature_values):
                feature_label = feature_types_label_in_order[i]
                if not feature_value in self.feature_types_dict[feature_label]:
                    raise ValueError("Illegal feature was found for segment {0}".format(symbol))
                symbol_feature_dict[feature_label] = feature_value
            self.feature_table_dict[symbol] = symbol_feature_dict

        for symbol in self.get_alphabet():
            from segment import Segment  # in order to prevent circular import
            self.segments_list.append(Segment(symbol))

    @classmethod
    def load(cls, feature_table_file_name):
        file = open(feature_table_file_name, "r")
        if splitext(feature_table_file_name)[1] == ".json":
            feature_table_dict = json.load(file)
        else:
            feature_table_dict = FeatureTable._get_feature_table_dict_form_csv(file)
        file.close()
        return cls(feature_table_dict)

    @staticmethod
    def _get_feature_table_dict_form_csv(file):
        feature_table_dict = dict()
        feature_table_dict['feature'] = list()
        feature_table_dict['feature_table'] = dict()
        lines = file.readlines()
        lines = [x.strip() for x in lines]
        feature_label_list = lines[0][1:].split(",")  #first line, ignore firt comma (,cons, labial..)
        feature_table_dict['feature'] = list()
        for label in feature_label_list:
            feature_table_dict['feature'].append({'label': label, 'values': ['-', '+']})

        for line in lines[1:]:
            values_list = line.split(',')
            feature_table_dict['feature_table'][values_list[0]] = values_list[1:]

        return feature_table_dict

    def get_number_of_features(self):
        return len(self.feature_types_dict)

    def get_features(self):
        return list(self.feature_types_dict.keys())

    def get_random_value(self, feature):
        return choice(self.feature_types_dict[feature])

    def get_alphabet(self):
        return list(self.feature_table_dict.keys())

    def get_segments(self):
        return deepcopy(self.segments_list)

    def get_random_segment(self):
        return choice(self.get_alphabet())

    def get_ordered_feature_vector(self, char):
        return [self[char][self.feature_order_dict[i]] for i in range(self.get_number_of_features())]

    def is_valid_feature(self, feature_label):
        return feature_label in self.feature_types_dict

    def is_valid_symbol(self, symbol):
        return symbol in self.feature_table_dict

    def __str__(self):
        values_string_io = StringIO()
        print("Feature Table with {0} features and {1} segments:".format(self.get_number_of_features(),
                                                                        len(self.get_alphabet())), end="\n",
                                                                        file=values_string_io)

        print("{:20s}".format("Segment/Feature"), end="", file=values_string_io)
        for i in list(range(len(self.feature_order_dict))):
            print("{:10s}".format(self.feature_order_dict[i]), end="", file=values_string_io)
        print("", file=values_string_io)  # new line
        for segment in sorted(self.feature_table_dict.keys()):
            print("{:20s}".format(segment), end="", file=values_string_io)
            for i in list(range(len(self.feature_order_dict))):
                feature = self.feature_order_dict[i]
                print("{:10s}".format(self.feature_table_dict[segment][feature]), end="", file=values_string_io)
            print("", file=values_string_io)

        return values_string_io.getvalue()

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.feature_table_dict[item]
        if isinstance(item, int):
            return self.feature_table_dict[self.feature_order_dict[item]]
        else:
            segment, feature = item
            return self.feature_table_dict[segment][feature]

    def __len__(self):
        return len(self.segments_list)
