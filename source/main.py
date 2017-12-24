import sys
from os.path import join, split, abspath
import platform
import logging
from configuration import Configuration
from feature_table import FeatureTable
from constraint_set import ConstraintSet
from lexicon import Lexicon
from corpus import Corpus
from grammar import Grammar
from hypothesis import Hypothesis
from simulated_annealing import SimulatedAnnealing
from utils import set_configuration


if __name__ == '__main__':
    import simulations.vowel_harmony as current_simulation  # select simulation by simulations.[NAME]

    configuration = Configuration()
    configuration.load_configurations_from_dict(current_simulation.configurations_dict)

    simulation_number = 1
    if len(sys.argv) > 1:
        simulation_number = int(sys.argv[1])
        set_configuration("RANDOM_SEED", True)

    log_file_name = current_simulation.log_file_template.format(platform.node(), simulation_number)
    set_configuration("LOG_FILE_NAME", log_file_name)
    dir_name, _ = split(abspath(__file__))
    log_file_path = join(dir_name, "../logging/", log_file_name)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    file_log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', "%Y-%m-%d %H:%M:%S")
    file_log_handler = logging.FileHandler(log_file_path, mode='w')
    file_log_handler.setFormatter(file_log_formatter)
    logger.addHandler(file_log_handler)

    feature_tables_dir_path = join(dir_name, "tests/fixtures/feature_tables")
    constraint_sets_dir_path = join(dir_name, "tests/fixtures/constraint_sets")

    feature_table_file_path = join(feature_tables_dir_path, current_simulation.feature_table_file_name)
    feature_table = FeatureTable.load(feature_table_file_path)

    constraint_set_file_path = join(constraint_sets_dir_path, current_simulation.constraint_set_file_name)
    constraint_set = ConstraintSet.load(constraint_set_file_path)

    corpus = Corpus(current_simulation.corpus)

    data = corpus.get_words()
    max_word_length_in_data = max([len(word) for word in data])
    lexicon = Lexicon(data, max_word_length_in_data)

    grammar = Grammar(constraint_set, lexicon)
    hypothesis = Hypothesis(grammar, data)

    if hasattr(current_simulation, "target_energy"):
        target_energy = current_simulation.target_energy
    else:
        target_energy = None

    simulated_annealing = SimulatedAnnealing(hypothesis, target_energy)
    simulated_annealing.run()
