import json
import os

import click

from src.db.workout import models
from src.db.workout.workout import Workout
from src.scripts.dump_workout_data_store import WorkoutDataWithFilenameStore
from src.utils import db_utils, log


def process_new_workout(db, data):
    print(data.filename)
    if len(data.sources) == 0:
        print(f"No source info attached")
    workout = Workout(db, data)
    workout.insert_row()


def read_files():
    all_info = []
    for f in os.listdir("/home/nina/code/polar/polar-hr/data/output"):
        if not f.startswith("training-session"):
            continue

        with open(f"/home/nina/code/polar/polar-hr/data/output/{f}") as fi:
            all_info.append(WorkoutDataWithFilenameStore(json.load(fi), f))

    srt = lambda x: x.filename
    return sorted(all_info, key=srt)


def create_tables(database):
    with database.atomic():
        database.create_tables(models.get_all_models())
    # insert_equipment(database)


def drop_tables_and_types(database):
    types = []
    for table in tables():
        for name, field in table._meta.fields.items():
            if isinstance(field, models.EnumField):
                types.append(field)

    with database.atomic():
        database.drop_tables(tables(), cascade=True)
        for field in types:
            field.delete_type()


@click.command()
@click.option(
    "--clean", is_flag=True, default=False, help="Drop and recreate all tables"
)
def main(clean):
    logger = log.new_logger(is_dev=True)
    db = db_utils.DBConnection(logger).workout_db

    if clean:
        drop_tables_and_types(db)
        create_tables(db)
    data = read_files()
    for i in data:
        process_new_workout(db, i)


if __name__ == "__main__":
    main()
