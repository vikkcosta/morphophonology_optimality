from io import StringIO
from utils import get_feature_table


class Segment:
    def __init__(self, symbol):
        self.symbol = symbol
        self.hash = hash(self.symbol)

    def get_encoding_length(self):
        feature_table = get_feature_table()
        feature_dict = feature_table[self.symbol]
        return len(feature_dict)

    def has_feature_bundle(self, feature_bundle):
        feature_table = get_feature_table()
        items = feature_bundle.get_feature_dict().items()
        list_of_booleans = [item in feature_table[self.symbol].items() for item in items]
        has_feature_bundle_result = all(list_of_booleans)
        return has_feature_bundle_result

    def get_symbol(self):
        return self.symbol

    @staticmethod
    def intersect(x, y):
        """ Intersect two segments, a segment and a set, or two sets.

        :type x: Segment or set
        :type y: Segment or set
        """
        if isinstance(x, set):
            x, y = y, x  # if x is a set then maybe y is a segment, switch between them so that
                         # Segment.__and__ will take affect
        return x & y

    def __and__(self, other):
        """ Based on ```(17) symbol unification```(Riggle, 2004)

        :type other: Segment or set
        """
        if self == JOKER_SEGMENT:
            return other
        elif isinstance(other, set):
            if self.symbol in other:
                return self
        else:
            if self == other:
                return self
            elif other == JOKER_SEGMENT:
                return self
        return None

    def __eq__(self, other):
        if other is None:
            return False
        return self.symbol == other.symbol

    def __hash__(self):
        return self.hash

    def __str__(self):
        if hasattr(self, "feature_table"):
            values_string_io = StringIO()
            ordered_feature_vector = self.feature_table.get_ordered_feature_vector(self.symbol)

            for value in ordered_feature_vector:
                print(value, end=", ", file=values_string_io)
            return "Segment {0}[{1}]".format(self.symbol, values_string_io.getvalue()[:-2])
        else:
            return self.symbol

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.feature_dict[item]


NULL_SEGMENT = Segment("-")
JOKER_SEGMENT = Segment("*")
