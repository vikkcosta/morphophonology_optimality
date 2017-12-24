from utils import get_configuration, get_feature_table


class Corpus:
    def __init__(self, string_words):
        duplication_factor = get_configuration("CORPUS_DUPLICATION_FACTOR")
        n = len(string_words)
        duplication_factor_int = int(duplication_factor)
        duplication_factor_fraction = duplication_factor - int(duplication_factor)
        words_after_duplication = string_words * duplication_factor_int
        words_after_duplication.extend(string_words[:int(n*duplication_factor_fraction)])
        self.words = words_after_duplication

    def get_words(self):
        return self.words[:]

    def __str__(self):
        return "Corpus with {0} words".format(len(self))

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.words.__getitem__(item)

    def __len__(self):
        return len(self.words)
