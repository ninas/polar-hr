import json
import os

import click

from playhouse.migrate import *
from src.db.workout import models
from src.db.workout.workout import Workout
from src.scripts.dump_workout_data_store import WorkoutDataWithFilenameStore
from src.utils import db_utils, log
from playhouse.postgres_ext import *

(
    PostgresqlExtDatabase,
    IntervalField,
    DateTimeTZField,
    BinaryJSONField,
)


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


def zones(migrator):
    name_type = {
        "lower": IntegerField(null=True),
        "upper": IntegerField(null=True),
        "duration": IntervalField(null=True),
        "percentspentabove": FloatField(null=True),
    }
    columns = []
    for i in ["below_50", "50_60", "60_70", "70_80", "80_90", "90_100"]:
        for name, typ in name_type.items():
            columns.append(migrator.add_column("workouts", f"zone_{i}_{name}", typ))

    return columns


def move_zone_data(db):
    mapping = {
        models.ZoneType.BELOW_50: "below_50",
        models.ZoneType.FIFTY_60: "50_60",
        models.ZoneType.SIXTY_70: "60_70",
        models.ZoneType.SEVENTY_80: "70_80",
        models.ZoneType.EIGHTY_90: "80_90",
        models.ZoneType.NINETY_100: "90_100",
    }
    attr_map = {
        "lowerlimit": "lower",
        "higherlimit": "upper",
        "duration": "duration",
        "percentspentabove": "percentspentabove",
    }

    with db.atomic():
        workouts = {
            w.id: w for w in models.Workouts.select().order_by(models.Workouts.id)
        }

        for zone in models.HRZones.select().order_by(models.HRZones.workout_id):
            print(zone.workout_id, zone.zonetype)
            prefix = f"zone_{mapping[zone.zonetype]}"
            wrk = workouts[zone.workout_id]
            for old_a, new_a in attr_map.items():
                setattr(wrk, f"{prefix}_{new_a}", getattr(zone, old_a))

        for k, v in workouts.items():
            v.save()


def main():
    logger = log.new_logger(is_dev=True)
    db = db_utils.DBConnection(logger).workout_db
    migrator = PostgresqlMigrator(db)
    move_zone_data(db)
    # with db.atomic():
    # migrate(*zones(migrator))
    # migrator.add_column("workouts", "samples", BinaryJSONField(null=True)))


if __name__ == "__main__":
    main()
