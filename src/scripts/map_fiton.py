import csv
import json
import os
import pprint
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import cache

from peewee import prefetch

from src.db.workout import models
from src.db.workout.models import SourceType
from src.db.workout.source import Source
from src.db.workout.workout import ExistingWorkout
from src.scripts.dump_workout_data_store import DumpWorkoutDataStore
from src.scripts.polar_raw_data import *
from src.utils import log
from src.utils.db_utils import DBConnection
from src.workout_sources.fiton import Fiton

pp = pprint.PrettyPrinter(indent=4)
DEBUG = False
ignore_matches = {"2021-10-17 04:48:00+00:00"}


def read_fiton_data():
    data = {}
    with open(
        "/home/nina/code/polar/polar-hr/data/fiton.csv", encoding="utf-8-sig"
    ) as f:
        reader = csv.reader(f, delimiter=",")
        five_min = timedelta(minutes=5)
        for row in reader:
            workout_id, dur, _, created_at, updated_at, *args = row
            # times are in UTC
            start = datetime.strptime(created_at, "%m/%d/%y %H:%M")
            start = start.replace(tzinfo=timezone.utc)
            duration = timedelta(seconds=int(dur))
            if duration < five_min:
                continue
            data[start] = {
                "workout_id": workout_id,
                "duration": duration,
                "created": updated_at,
                "start": start,
            }
    return data


def get_fiton_workout(w_id):
    return Fiton.fetch_all_workout_data[w_id]


def map_by_date(data):
    date_only = defaultdict(list)
    for k, v in data.items():
        date_only[k.date()].append(k)

    for k, v in date_only.items():
        v.sort()

    return date_only


def merge_data(polar, fiton):
    fiton_by_date = map_by_date(fiton)
    polar_by_date = map_by_date(polar)
    polar_to_fiton = defaultdict(list)

    for dt in sorted(fiton.keys()):
        if dt.date() not in polar_by_date:
            print(f"Merge: No potential fiton workout found for time {dt}")
            continue
        if str(dt) in ignore_matches:
            continue
        if len(polar_by_date[dt.date()]) == 1:
            if DEBUG:
                print(dt)
                print(polar_by_date[dt.date()][0])
                print(fiton[dt]["created"])
                print(fiton[dt]["duration"])
                print(get_fiton_workout(fiton[dt]["workout_id"]))
                print("")
            polar_to_fiton[polar_by_date[dt.date()][0]].append(fiton[dt])
            continue

        potentials = polar_by_date[dt.date()]
        found = False
        for pot in potentials:
            if abs(dt - pot) <= timedelta(minutes=3):
                found = True
                polar_to_fiton[pot].append(fiton[dt])
                break

        if not found and DEBUG:
            print(dt)
            print([str(i) for i in potentials])
            print(fiton[dt]["created"])
            print(fiton[dt]["duration"])
            print("")

    if DEBUG:
        for k, v in polar_to_fiton.items():
            print(k)
            print(v)
            print("")

    return polar_to_fiton


class FitonToDB:
    def __init__(self, polar_to_fiton, polar, fiton):
        self.logger = log.new_logger(is_dev=True)
        self.db = DBConnection(self.logger).workout_db
        self.polar_to_fiton = polar_to_fiton
        self.polar = polar
        self.fiton = fiton

    def check_db_for_duplicates(self):
        with self.db.atomic():
            for k in self.polar_to_fiton:
                wrkout = self.polar[k]
                res = models.Workouts.get(models.Workouts.starttime == k)
                if len(res.sources) > 0:
                    print(res, [i for i in res.sources])
                    print(self.polar_to_fiton[k])
                    print("")

    def update_db(self):
        for workout_start, fiton_data in polar_to_fiton.items():
            # We know these workouts are already in the db, so just search for them directly
            wrkout = ExistingWorkout(self.db, workout_start, self.logger)

            print("Adding:")
            print(workout_start)
            print(fiton_data)
            wrkout.add_sources([f"fiton:{f['workout_id']}" for f in fiton_data])


if __name__ == "__main__":

    def transform_func(data, filename):
        if "note" in data and "fiton" in data["note"]:
            del data["note"]

    polar = read_polar_dir(transform_func)
    fiton = read_fiton_data()
    polar_to_fiton = merge_data(polar, fiton)
    # check_db_for_duplicates(polar_to_fiton, polar, fiton)
    f = FitonToDB(polar_to_fiton, polar, fiton)
    f.update_db()
