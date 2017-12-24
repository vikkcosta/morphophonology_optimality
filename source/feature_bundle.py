import logging
from random import choice
from utils import get_configuration, get_feature_table


logger = logging.getLogger(__name__)



class FeatureBundle:
    __slots__ = ["feature_dict", "feature_table"]

    def __init__(self, feature_dict):
        self.feature_table = get_feature_table()

        for feature in feature_dict.keys():
            if not self.feature_table.is_valid_feature(feature):
                raise ValueError("Illegal feature: {0}".format(feature))

        self.feature_dict = feature_dict

    def get_encoding_length(self):
        return 2 * len(self.feature_dict)

    def get_keys(self):
        return list(self.feature_dict.keys())

    def get_feature_dict(self):
        return self.feature_dict

    def augment_feature_bundle(self):
        if len(self.feature_dict) < get_configuration("MAX_FEATURES_IN_BUNDLE"):
            all_feature_labels = self.feature_table.get_features()
            feature_labels_in_feature_bundle = self.feature_dict.keys()
            available_feature_labels = list(set(all_feature_labels) - set(feature_labels_in_feature_bundle))
            if available_feature_labels:
                feature_label = choice(available_feature_labels)
                self.feature_dict[feature_label] = self.feature_table.get_random_value(feature_label)
                return True
        return False

    @classmethod
    def generate_random(cls):
        feature_table = get_feature_table()
        if get_configuration("INITIAL_NUMBER_OF_FEATURES") > feature_table.get_number_of_features():
            raise ValueError("INITIAL_NUMBER_OF_FEATURES is bigger from number of available features")

        feature_dict = dict()
        available_feature_labels = feature_table.get_features()
        for i in range(get_configuration("INITIAL_NUMBER_OF_FEATURES")):
            feature_label = choice(available_feature_labels)
            feature_dict[feature_label] = feature_table.get_random_value(feature_label)
            available_feature_labels.remove(feature_label)
        return FeatureBundle(feature_dict)

    def __eq__(self, other):
        return self.feature_dict == other.feature_dict

    def __str__(self):
        return str(self.feature_dict)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.feature_dict[item]
