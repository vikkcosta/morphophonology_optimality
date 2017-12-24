import time
import os
from collections import defaultdict
from os.path import abspath, join, split
from sys import platform

MAC_OS_PLATFORM_NAME = "darwin"

dirname, filename = split(abspath(__file__))
dot_files_folder_path = join(dirname, "../logging/dot_files")


debug_print = print


def is_local_machine():
    current_platform = platform
    if current_platform == MAC_OS_PLATFORM_NAME:
        return True
    return False


def print_empty_line():
    print()


def write_to_dot(transducer, file_name):
    path, file = split(file_name)
    new_path = join(dot_files_folder_path, path)
    if not os.path.exists(new_path):
        os.makedirs(new_path)
    if hasattr(transducer, "dotFormat"):
        draw_string = transducer.dotFormat()
        open(join(dot_files_folder_path, file_name + ".dot"), "w").write(draw_string)
    elif hasattr(transducer, "draw"):
        open(os.path.join(dot_files_folder_path, file_name + ".dot"), "w").write(transducer.draw())

    else:
        with open(join(dot_files_folder_path, file_name+".dot"), "w") as file_:
            file_.write(transducer.dot_representation())




run_times_by_function_names = defaultdict(list)



def timeit(method):
    def timed(*args, **kw):
        start_time = time.time()
        result = method(*args, **kw)
        end_time = time.time()
        delta = end_time - start_time
        run_times_by_function_names[method.__name__].append(delta)
        return result
    return timed


def get_time_string(time_):
    if time_ > 1:
        time_string = "{0:.1f} seconds".format(time_)
        if time_ > 60:
            from simulated_annealing import _pretty_runtime_str
            time_string = _pretty_runtime_str(time_)
    else:
        time_ *= 1000
        if time_ > 1:
            time_string = "{0:.0f} milliseconds".format(time_)
        else:
            time_ *= 1000
            time_string = "{0:.0f} microseconds".format(time_)

    return time_string


def get_statistics():
    statistics = dict()
    for function_name in run_times_by_function_names:
        statistics[function_name] = get_time_string(sum(run_times_by_function_names[function_name]))
    return statistics

N = (10**1)

@timeit
def function_to_time():
    x = 0
    for i in range(N):
        x += 1
    return x

if __name__ == "__main__":
    function_to_time()


