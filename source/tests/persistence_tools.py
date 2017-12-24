from os.path import split, abspath, join
from feature_table import FeatureTable
import pickle

tests_dir_path, filename = split(abspath(__file__))

pickled_results_folder_path = join(tests_dir_path, "pickled_results")

def write_pickle(obj, file_name):
    file = open(_get_pickle_full_path(file_name), "wb")
    pickle.dump(obj, file)
    file.close()


def get_pickle(file_name):
    file = open(_get_pickle_full_path(file_name), "rb")
    obj = pickle.load(file)
    file.close()
    return obj


def _get_pickle_full_path(file_name):
    return join(pickled_results_folder_path, file_name+".pkl")


fixtures_dir_path = join(tests_dir_path, "fixtures")
constraint_sets_dir_path = join(fixtures_dir_path, "constraint_sets")
corpora_dir_path = join(fixtures_dir_path, "corpora")
feature_table_dir_path = join(fixtures_dir_path, "feature_tables")


def get_constraint_set_fixture(constraint_set_file_name):
    return join(constraint_sets_dir_path, constraint_set_file_name)


def get_corpus_fixture(corpus_file_name):
    return join(corpora_dir_path, corpus_file_name)


def get_feature_table_fixture(feature_table_file_name):
    return join(feature_table_dir_path, feature_table_file_name)


def get_feature_table_by_fixture(feature_table_file_name):
    return FeatureTable.load(get_feature_table_fixture(feature_table_file_name))



