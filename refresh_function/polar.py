import json, isodate
from peewee import fn
from datetime import timedelta
from functools import cache

from utils import gcp_utils
from db.sources import models as source_models
from db.workout import models as workout_models
from scripts.workout import Workout

from .polar_api import PolarAPI

@cache
def source_db():
    source_models.database.init(
        "source_input",
        host="35.222.196.247",
        user="postgres",
        password=gcp_utils.get_secret("db_workout"),
    )
    source_models.database.connect()
    return source_models.database

@cache
def workout_db():
    workout_models.database.init(
        "workout_data",
        host="34.28.182.87",
        user="admin",
        password=gcp_utils.get_secret("db_workout"),
    )
    workout_models.database.connect()
    return workout_models.database

def get_sources(earliest):
    results = source_models.SourceInput.select().where(source_models.SourceInput.created >= earliest).execute()
    print(results)
    for i in results:
        print(i)
    return results

def get_last_saved_workout_date():
    workout_db()
    return workout_models.Workouts.select(fn.MAX(workout_models.Workouts.starttime)).scalar()


def map_data(data, sources):
    # For each source, we want the workout where it was created after the start time, but before the start time of the next workout

    s_i = 0
    max_start = get_last_saved_workout_date()
    updated_workouts = []
    for workout in data:
        if max_start >= workout.start_time:
            continue
        added = False
        for i, source in enumerate(sources[s_i:]):
            if (
                workout.start_time < source.created and
                abs(source.created - workout.end_time) < timedelta(minutes=5) and
                (
                    len(sources) == i + 1 or
                    workout.created < sources[i+1].start_time
                )
            ):
                workout.add_source(source)
                updated_workouts.append(workout)
                s_i = i+1
                added = True
                print(f"Matched!")
                print(f"Workout: {workout}")
                print(f"Source: {source}")
                break

        if not added:
            print(f"didn't find a match: {workout}")

    return updated_workouts

def save_to_db(workouts):
    for workout in workouts:
        w = Workout(workout_db(), workout)
        w.insert_row()

if __name__ == "__main__":
    source_db()
    api = PolarAPI()
    print(api)
    data = api.exercises
    if len(data) > 0:
        srcs = get_sources(data[0].start_time)
        workouts = map_data(data, srcs)
        save_to_db(workouts)
