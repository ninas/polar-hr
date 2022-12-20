import json
import os
from collections import defaultdict

from src.scripts.dump_workout_data_store import DumpWorkoutDataStore


def read_polar_dir(transform_func=None):
    dd = lambda x: defaultdict(list)

    data = defaultdict(dd)
    all_info = {}
    for f in os.listdir("/home/nina/code/polar/polar-hr/data/polar"):
        if not f.startswith("training"):
            continue
        start, d = read_polar_data(f, transform_func)
        all_info[start] = d
    return all_info


def read_polar_data(f, transform_func):
    with open(f"/home/nina/code/polar/polar-hr/data/polar/{f}") as fi:
        contents = json.load(fi)
        if transform_func is not None:
            transform_func(contents, f)
        dump_wd = DumpWorkoutDataStore(contents, f)
    return dump_wd.start_time, dump_wd
