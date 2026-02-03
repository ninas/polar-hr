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
from src.scripts.dump_workout_data_store import DumpWorkoutDataStore
from src.scripts.polar_raw_data import *
from src.utils import log
from src.utils.db_utils import DBConnection

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


def read_workout_data():
    workouts = {}
    with open(
        "/home/nina/code/polar/polar-hr/data/fiton_enriched.json", encoding="utf-8-sig"
    ) as f:
        data = json.loads(f.read())
    for workout in data:
        if workout["workoutID"] in workouts:
            continue

        tags = {"fiton"}
        for cat in workout["workoutData"]["categoryList"]:
            tags.add(cat["categoryNameEN"].lower().strip())
        for equip in workout["workoutData"]["equipments"]:
            if equip["nameEN"] == "mat":
                continue
            if equip["nameEN"] == "dumbbells":
                equip["nameEN"] = "weights"
            tags.add(equip["nameEN"].lower().strip())

        workouts[workout["workoutID"]] = {
            "name": workout["workoutName"].strip(),
            "creator": workout["trainerName"].strip(),
            "sourceType": SourceType.FITON,
            "url": f"https://app.fitonapp.com/browse/workout/{workout['workoutID']}",
            "tags": tags,
        }

    return workouts


def map_by_date(data):
    date_only = defaultdict(list)
    for k, v in data.items():
        date_only[k.date()].append(k)

    for k, v in date_only.items():
        v.sort()

    return date_only


def merge_data(polar, fiton, fiton_workouts):
    fiton_by_date = map_by_date(fiton)
    polar_by_date = map_by_date(polar)
    polar_to_fiton = defaultdict(list)

    for dt in sorted(fiton.keys()):
        if dt.date() not in polar_by_date:
            print(f"Merge: No potential fiton workout found for time {dt}")
            continue
        if str(dt) in ignore_matches:
            print("skipping")
            continue
        if len(polar_by_date[dt.date()]) == 1:
            # print(dt)
            # print(polar_by_date[dt.date()][0])
            # print(fiton[dt]["created"])
            # print(fiton[dt]["duration"])
            # print(fiton_workouts[fiton[dt]["workout_id"]])
            # print("")
            polar_to_fiton[polar_by_date[dt.date()][0]].append(fiton[dt])
            continue

        potentials = polar_by_date[dt.date()]
        found = False
        for pot in potentials:
            if abs(dt - pot) <= timedelta(minutes=3):
                found = True
                polar_to_fiton[pot].append(fiton[dt])
                break

        if not found:
            print(dt)
            print([str(i) for i in potentials])
            print(fiton[dt]["created"])
            print(fiton[dt]["duration"])
            print("")

    for k, v in polar_to_fiton.items():
        print(k)
        print(v)
        print("")

    return polar_to_fiton


def check_db_for_duplicates(polar_to_fiton, polar, fiton):
    logger = log.new_logger(is_dev=True)

    db = DBConnection(logger).workout_db

    with db.atomic():
        for k in polar_to_fiton:
            wrkout = polar[k]
            res = models.Workouts.get(models.Workouts.starttime == k)
            if len(res.sources) > 0:
                print(res, [i for i in res.sources])
                print(polar_to_fiton[k])
                print("")


def write_out(polar, location):
    if not os.path.exists(location):
        os.makedirs(location)

    for k, v in polar.items():
        if DEBUG:
            print(v.note, v.filename)
            pp.pprint(v)
        with open(os.path.join(location, v.filename), "w") as f:
            f.write(json.dumps(v.as_dict(), indent=4, sort_keys=True))


if __name__ == "__main__":

    def transform_func(data, filename):
        if "note" in data and "fiton" in data["note"]:
            del data["note"]

    polar = read_polar_dir(transform_func)
    fiton = read_fiton_data()
    workouts = read_workout_data()
    polar_to_fiton = merge_data(polar, fiton, workouts)
    # check_db_for_duplicates(polar_to_fiton, polar, fiton)
    # confirm_notes(polar)
    # write_out(polar, "data/fiton_output")
