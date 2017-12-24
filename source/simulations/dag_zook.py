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
    "INSERT_CONSTRAINT": 0,
    "REMOVE_CONSTRAINT": 0,
    "DEMOTE_CONSTRAINT": 1,
    "INSERT_FEATURE_BUNDLE_PHONOTACTIC_CONSTRAINT": 0,
    "REMOVE_FEATURE_BUNDLE_PHONOTACTIC_CONSTRAINT": 0,
    "AUGMENT_FEATURE_BUNDLE": 0,

    # "constraint_insertion_weights
    "DEP_FOR_INSERT": 0,
    "MAX_FOR_INSERT": 0,
    "IDENT_FOR_INSERT": 0,
    "PHONOTACTIC_FOR_INSERT": 0,

    "MAX_NUM_OF_INNER_STATES": 2,
    "MIN_NUM_OF_INNER_STATES": 1,

    "RANDOM_SEED": False,
    "SEED": 4,
    "INITIAL_TEMPERATURE": 200,
    "COOLING_PARAMETER": 0.99995,
    "STEPS_LIMITATION": float("inf"),
    "THRESHOLD": 10**-1,

    "ALLOW_CANDIDATES_WITH_CHANGED_SEGMENTS": True,
    "INITIAL_NUMBER_OF_BUNDLES_IN_PHONOTACTIC_CONSTRAINT": 1,
    "MIN_FEATURE_BUNDLES_IN_PHONOTACTIC_CONSTRAINT": 1,
    "MAX_FEATURE_BUNDLES_IN_PHONOTACTIC_CONSTRAINT": 3,
    "DATA_ENCODING_LENGTH_MULTIPLIER": 25,
    "GRAMMAR_ENCODING_LENGTH_MULTIPLIER": 1,
    "MAX_NUMBER_OF_CONSTRAINTS_IN_CONSTRAINT_SET": float("INF"),
    "DEBUG_LOGGING_INTERVAL": 50,
    "SLACK_NOTIFICATION_INTERVAL": 50_000,
    "CORPUS_DUPLICATION_FACTOR": 1,
    "CLEAR_MODULES_CACHING_INTERVAL": 100

}

log_file_template = "{}_dag_zook_devoicing_{}.txt"
corpus = ['dagdod', 'daggos', 'dagzook',
         'kattod', 'katkos', 'katsook',
         'dottod', 'dotkos', 'dotsook',
         'koddod', 'kodgos', 'kodzook',
         'gastod', 'gaskos', 'gassook',
         'tozdod', 'tozgos', 'tozzook',
         'atadod', 'atagos', 'atazook',
         'asodod', 'asogos', 'asozook',
          'dag', 'kat', 'dot', 'kod', 'gas', 'toz', 'ata', 'aso']
feature_table_file_name = "plural_english_feature_table.json"
constraint_set_file_name = "dag_zook_devoicing_permutations_constraint_set.json"
target_energy = 4_832



