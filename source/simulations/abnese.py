configurations_dict = {

    "MUTATE_LEXICON": 1,
    "MUTATE_CONSTRAINT_SET": 1,

    "COMBINE_EMISSIONS": 1,
    "ADVANCE_EMISSION": 1,
    "CLONE_STATE": 1,
    "CLONE_EMISSION": 1,

    "ADD_STATE": 1,
    "REMOVE_STATE": 1,
    "ADD_TRANSITION": 1,
    "REMOVE_TRANSITION": 1,

    "ADD_SEGMENT_TO_EMISSION": 1,
    "REMOVE_SEGMENT_FROM_EMISSION": 1,
    "CHANGE_SEGMENT_IN_EMISSION": 1,

    "ADD_EMISSION_TO_STATE": 1,
    "REMOVE_EMISSION_FROM_STATE": 1,

    # constraint_set_mutation_weights
    "INSERT_CONSTRAINT": 1,
    "REMOVE_CONSTRAINT": 1,
    "DEMOTE_CONSTRAINT": 1,
    "INSERT_FEATURE_BUNDLE_PHONOTACTIC_CONSTRAINT": 1,
    "REMOVE_FEATURE_BUNDLE_PHONOTACTIC_CONSTRAINT": 1,
    "AUGMENT_FEATURE_BUNDLE": 0,

    # "constraint_insertion_weights
    "DEP_FOR_INSERT": 1,
    "MAX_FOR_INSERT": 1,
    "IDENT_FOR_INSERT": 0,
    "PHONOTACTIC_FOR_INSERT": 1,

    "MAX_NUM_OF_INNER_STATES": 2,
    "MIN_NUM_OF_INNER_STATES": 1,

    "INITIAL_NUMBER_OF_FEATURES": 1,
    "MAX_FEATURES_IN_BUNDLE": float("inf"),
    "MIN_NUMBER_OF_CONSTRAINTS_IN_CONSTRAINT_SET": 1,
    "RANDOM_SEED": True,
#    "SEED": 3,
    "INITIAL_TEMPERATURE": 50,
    "COOLING_PARAMETER": 0.99995,
    "STEPS_LIMITATION": float("inf"),
    "THRESHOLD": 10**-1,

    "ALLOW_CANDIDATES_WITH_CHANGED_SEGMENTS": False,
    "INITIAL_NUMBER_OF_BUNDLES_IN_PHONOTACTIC_CONSTRAINT": 1,
    "MIN_FEATURE_BUNDLES_IN_PHONOTACTIC_CONSTRAINT": 1,
    "MAX_FEATURE_BUNDLES_IN_PHONOTACTIC_CONSTRAINT": 3,
    "DATA_ENCODING_LENGTH_MULTIPLIER": 25,
    "GRAMMAR_ENCODING_LENGTH_MULTIPLIER": 1,
    "MAX_NUMBER_OF_CONSTRAINTS_IN_CONSTRAINT_SET": float("INF"),
    "DEBUG_LOGGING_INTERVAL": 50,
    "CORPUS_DUPLICATION_FACTOR": 1,
    "LOG_LEXICON_WORDS": False,
    "CLEAR_MODULES_CACHING_INTERVAL": 1_000
}

log_file_template = "{}_abnese_50_0_99995_0_01_{}.txt"
corpus = ['aababaabab', 'aabababaa', 'aabababaab', 'aababababa', 'aababababab', 'aababaabaab', 'aababaaabaa', 'aabababaaaab', 'aababababaa', 'aabababababaa', 'aabaaabab', 'aabababaa', 'baabab', 'babaa', 'babaab', 'bababa', 'bababab', 'baabaab', 'baaabaa', 'babaaaab', 'bababaa', 'babababaa', 'aaabab', 'ababaa']

feature_table_file_name = "abnese_feature_table.json"
constraint_set_file_name = "faith_constraint_set.json"
target_energy = 3_316



#initial: 3,497