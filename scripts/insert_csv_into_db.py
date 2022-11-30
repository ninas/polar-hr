import os, json
import click


from utils.gcp_utils import get_secret, upload_to_cloud_storage
from db import models
from .workout import Workout


def process_new_workout(db, data):
    if "note" not in data:
        print(f"No extra info attached {data['filename']}")
    print(data["filename"])
    workout = Workout(db, data)
    workout.insert_row()


def read_files():
    all_info = []
    for f in os.listdir("/home/nina/code/polar/polar-hr/output"):
        if not f.startswith("training"):
            continue

        with open(f"/home/nina/code/polar/polar-hr/output/{f}") as fi:
            all_info.append(json.load(fi))

    srt = lambda x: x["filename"]
    return sorted(all_info, key=srt)


def tables():
    return [
        models.HRZones,
        models.Equipment,
        models.Tags,
        models.Sources,
        models.Sources.tags.get_through_model(),
        models.Workouts,
        models.Workouts.sources.get_through_model(),
        models.Workouts.equipment.get_through_model(),
        models.Workouts.tags.get_through_model()
    ]


def create_tables(database):
    with database.atomic():
        database.create_tables(tables())
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
    models.database.init(
        "workout_data",
        host="34.28.182.87",
        user="admin",
        password=get_secret("db_workout"),
    )
    models.database.connect()

    if clean:
        drop_tables_and_types(models.database)
        create_tables(models.database)
    data = read_files()
    for i in data:
        process_new_workout(models.database, i)


if __name__ == "__main__":
    main()
