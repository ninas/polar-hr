from peewee import fn
from playhouse.db_url import connect
from datetime import timedelta
from functools import cache

from src.utils import gcp_utils
from src.db.sources import models as source_models
from src.db.workout import models as workout_models
from src.db.workout.workout import Workout

from src.polar_api.polar_api import PolarAPI

UNIX_SOCKET_PATH = "/cloudsql/"


@cache
def source_db():
    source_models.database.init(
        gcp_utils.fetch_config("source_db/db_name"),
        host=UNIX_SOCKET_PATH + gcp_utils.fetch_config("source_db/gcp_path"),
        user=gcp_utils.fetch_config("source_db/username"),
        password=gcp_utils.get_secret("db_workout"),
    )
    source_models.database.connect()
    return source_models.database


@cache
def workout_db():
    print("in db func")
    workout_models.database.init(
        gcp_utils.fetch_config("workout_db/db_name"),
        host=UNIX_SOCKET_PATH + gcp_utils.fetch_config("workout_db/gcp_path"),
        user=gcp_utils.fetch_config("workout_db/username"),
        password=gcp_utils.get_secret("db_workout"),
    )
    workout_models.database.connect()
    print("connected")
    return workout_models.database


def get_sources(earliest):
    results = (
        source_models.SourceInput.select()
        .where(source_models.SourceInput.created >= earliest)
        .execute()
    )
    print(results)
    for i in results:
        print(i)
    return results


def get_last_saved_workout_date():
    print("last saved")
    db = workout_db()
    print(db)
    with db.atomic():
        return workout_models.Workouts.select(
            fn.MAX(workout_models.Workouts.starttime)
        ).scalar()


def map_data(data, sources):
    # For each source, we want the workout where it was created after the start time, but before the start time of the next workout

    print("starting mapping")
    s_i = 0
    max_start = get_last_saved_workout_date()
    print("last saved")
    updated_workouts = []
    for workout in data:
        print("start loop")
        if max_start >= workout.start_time:
            print(f"skipping {workout}")
            continue
        added = False
        for i, source in enumerate(sources[s_i:]):
            print("enumerating sources")
            if (
                workout.start_time < source.created
                and abs(source.created - workout.end_time) < timedelta(minutes=5)
                and (
                    len(sources) == i + 1 or workout.start_time < sources[i + 1].created
                )
            ):
                print("in if")
                workout.add_source(source)
                updated_workouts.append(workout)
                s_i = i + 1
                added = True
                print(f"Matched!")
                print(f"Workout: {workout}")
                print(f"Source: {source}")
                break

        if not added:
            print(f"didn't find a match: {workout}")

    print(updated_workouts)
    return updated_workouts


def save_to_db(workouts):
    for workout in workouts:
        print("starting insert")
        w = Workout(workout_db(), workout)
        w.insert_row()
        print("row inserted")
        break


if __name__ == "__main__":
    source_db()
    api = PolarAPI()
    print(api)
    data = api.exercises
    if len(data) > 0:
        srcs = get_sources(data[0].start_time)
        workouts = map_data(data, srcs)
        save_to_db(workouts)
