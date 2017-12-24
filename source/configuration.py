from io import StringIO
from copy import deepcopy
from singelton import Singleton


class Configuration(metaclass=Singleton):
    def __init__(self):
        self.configurations_dict = dict()

    def reset_to_original_configurations(self):
        self.configurations_dict = deepcopy(self.initial_configurations_dict)

    def __getitem__(self, key):
        return self.configurations_dict[key]

    def __setitem__(self, key, value):
        self.configurations_dict[key] = value

    def load_configurations_from_dict(self, configurations_dict):
        self.configurations_dict = configurations_dict
        self.initial_configurations_dict = deepcopy(self.configurations_dict)

    def __str__(self):
        values_str_io = StringIO()
        print("Configurations:", end="\n", file=values_str_io)
        for (key, value) in sorted(self.configurations_dict.items()):
            value_string = ""
            if type(value) is dict:
                for (secondary_key, secondary_value) in self.configurations_dict[key].items():
                    value_string += (len(key)+2) * " " + "{}: {}\n".format(secondary_key, secondary_value) #manual justification
                value_string = value_string.strip()
            else:
                value_string = str(value)
            print("{}: {}".format(key, value_string), end="\n", file=values_str_io)

        return values_str_io.getvalue().strip()

