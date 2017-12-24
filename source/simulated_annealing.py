import logging
from math import exp
from random import choice
import random
from datetime import timedelta
import time
import re
from utils import get_configuration, set_configuration
from os import getpid
from grammar import Grammar
from constraint_set import ConstraintSet
from constraint import Constraint
from word import Word
from configuration import Configuration
from utils import send_to_webhook

logger = logging.getLogger(__name__)
process_id = getpid()


class SimulatedAnnealing:
    def __init__(self, traversable_hypothesis, target_energy):
        self.current_hypothesis = traversable_hypothesis
        self.target_energy = target_energy
        self.step = 0
        self.current_temperature = None
        self.threshold = None
        self.cooling_parameter = None
        self.current_hypothesis_energy = None
        self.neighbor_hypothesis = None
        self.neighbor_hypothesis_energy = None
        self.step_limitation = None
        self.number_of_expected_steps = None
        self.start_time = None
        self.previous_interval_time = None
        self.previous_interval_energy = None

    def run(self):
        self._before_loop()

        while (self.current_temperature > self.threshold) and (self.step != self.step_limitation):
            self._make_step()

        self._after_loop()
        return self.step, self.current_hypothesis

    def _before_loop(self):
        self.start_time = time.time()
        self.previous_interval_time = self.start_time
        logger.info("Process Id: {}".format(process_id))
        if get_configuration("RANDOM_SEED"):
            seed = choice(range(1, 1000))
            set_configuration("SEED", seed)
            logger.info("Seed: {} - randomly selected".format(seed))
        else:
            seed = get_configuration("SEED")
            logger.info("Seed: {} - specified".format(seed))
        random.seed(3)
        #random.seed(seed)
        configurations = Configuration()
        logger.info(configurations)
        logger.info(self.current_hypothesis.grammar.feature_table)

        self.step_limitation = get_configuration("STEPS_LIMITATION")
        if self.step_limitation != float("inf"):
            self.number_of_expected_steps = self.step_limitation
        else:
            self.number_of_expected_steps = self._calculate_num_of_steps()

        logger.info("Number of expected steps is: {:,}".format(self.number_of_expected_steps))
        self.current_hypothesis_energy = self.current_hypothesis.get_energy()
        if self.current_hypothesis_energy == float("INF"):
            raise ValueError("first hypothesis energy can not be INF")

        self._log_hypothesis_state()
        self.previous_interval_energy = self.current_hypothesis_energy
        self.current_temperature = get_configuration("INITIAL_TEMPERATURE")
        self.threshold = get_configuration("THRESHOLD")
        self.cooling_parameter = get_configuration("COOLING_PARAMETER")

    def _make_step(self):
        self.step += 1
        self.current_temperature *= self.cooling_parameter

        self._check_for_intervals()

        mutation_result, neighbor_hypothesis = self.current_hypothesis.get_neighbor()
        if not mutation_result:
            return  # mutation failed - the neighbor hypothesis is the same as current hypothesis

        self.neighbor_hypothesis = neighbor_hypothesis
        self.neighbor_hypothesis_energy = self.neighbor_hypothesis.get_energy()

        energy_delta = self.neighbor_hypothesis_energy - self.current_hypothesis_energy

        if energy_delta > 0:
            switching_probability = exp(-energy_delta / self.current_temperature)
        else:  # neighbor hypothesis energy is smaller then current hypothesis energy - obvious switch
            switching_probability = 1

        random_between_0_and_1 = random.random()
        is_to_switch_hypothesis = (random_between_0_and_1 < switching_probability)

        if is_to_switch_hypothesis:
            self.current_hypothesis = self.neighbor_hypothesis
            self.current_hypothesis_energy = self.neighbor_hypothesis_energy

    def _after_loop(self):
        current_time = time.time()
        logger.info("*"*10 + " Final Hypothesis " + "*"*10)
        self._log_hypothesis_state()
        logger.info("simulated annealing runtime was: {}".format(_pretty_runtime_str(current_time - self.start_time)))

    def _check_for_intervals(self):
        if not self.step % get_configuration("DEBUG_LOGGING_INTERVAL"):
            self._debug_interval()
        if not self.step % get_configuration("SLACK_NOTIFICATION_INTERVAL"):
            self. _send_hypothesis_state_to_slack()
        if not self.step % get_configuration("CLEAR_MODULES_CACHING_INTERVAL"):
            self.clear_modules_caching()

    def _debug_interval(self):
        current_time = time.time()
        logger.info("\n"+"-"*125)
        percentage_completed = 100 * float(self.step)/float(self.number_of_expected_steps)
        logger.info("Step {0:,} of {1:,} ({2:.2f}%)".format(self.step, self.number_of_expected_steps,
                                                            percentage_completed))
        logger.info("-" * 80)
        elapsed_time = current_time - self.start_time
        logger.info("Time from simulation start: {}".format(_pretty_runtime_str(elapsed_time)))
        crude_expected_time = elapsed_time * (100/percentage_completed)
        logger.info("Expected simulation time: {} ".format(_pretty_runtime_str(crude_expected_time)))
        logger.info("Current temperature: {}".format(self.current_temperature))
        self._log_hypothesis_state()
        logger.info("Energy difference from last interval: {}".format(self.current_hypothesis_energy - self.previous_interval_energy))
        logger.info("Distance from target energy: {}".format(self.current_hypothesis_energy - self.target_energy))

        self.previous_interval_energy = self.current_hypothesis_energy
        time_from_last_interval = current_time - self.previous_interval_time
        logger.info("Time from last interval: {}".format(_pretty_runtime_str(time_from_last_interval)))
        logger.info("Time to finish based on current interval: {}".format(self.by_interval_time(time_from_last_interval)))
        self.previous_interval_time = current_time

        #write_to_dot(self.current_hypothesis.grammar.lexicon.hmm, f"current_hypothesis_hmm_{self.step}")

    def by_interval_time(self, time_from_last_interval):
        number_of_remaining_steps = self.number_of_expected_steps - self.step
        number_of_remaining_intervals = int(number_of_remaining_steps/get_configuration("DEBUG_LOGGING_INTERVAL"))
        expected_time = number_of_remaining_intervals * time_from_last_interval
        return _pretty_runtime_str(expected_time)

    def _send_hypothesis_state_to_slack(self):
        log_file_name = get_configuration("LOG_FILE_NAME")
        message = f"{log_file_name}\n"
        message += "Grammar with: {}\n".format(self.current_hypothesis.grammar.constraint_set)
        message += "{}\n".format(self.current_hypothesis.grammar.lexicon)
        message += "Parse: {}\n".format(self.current_hypothesis.get_recent_data_parse())
        message += "{}\n".format(self.current_hypothesis.get_recent_energy_signature())
        message += "HMM:\n"
        for line in self.current_hypothesis.grammar.lexicon.hmm.get_log_lines():
            message += f"{line}:\n"
        send_to_webhook(message)


    def _log_hypothesis_state(self):
        logger.info("Grammar with: {}:".format(self.current_hypothesis.grammar.constraint_set))
        logger.info("{}".format(self.current_hypothesis.grammar.lexicon))
        logger.info("Parse: {}".format(self.current_hypothesis.get_recent_data_parse()))
        logger.info(self.current_hypothesis.get_recent_energy_signature())
        logger.info("HMM:")
        for line in self.current_hypothesis.grammar.lexicon.hmm.get_log_lines():
            logger.info(line)

        
    @staticmethod
    def _calculate_num_of_steps():
        step = 0
        temp = get_configuration("INITIAL_TEMPERATURE")
        while temp > get_configuration("THRESHOLD"):
            step += 1
            temp *= get_configuration("COOLING_PARAMETER")
        return step


    def clear_modules_caching(self):
        Grammar.clear_caching()
        ConstraintSet.clear_caching()
        Constraint.clear_caching()
        Word.clear_caching()


def _pretty_runtime_str(run_time_in_seconds):
    time_delta = timedelta(seconds=run_time_in_seconds)
    timedelta_string = str(time_delta)

    m = re.search('(\d* (days|day), )?(\d*):(\d*):(\d*)', timedelta_string)
    days_string = m.group(1)
    hours = int(m.group(3))
    minutes = int(m.group(4))
    seconds = int(m.group(5))

    if days_string:
        days_string = days_string[:-2]
        return "{}, {} hours, {} minutes, {} seconds".format(days_string, hours, minutes, seconds)
    elif hours:
        return "{} hours, {} minutes, {} seconds".format(hours, minutes, seconds)
    elif minutes:
        return "{} minutes, {} seconds".format(minutes, seconds)
    else:
        return "{} seconds".format(seconds)



