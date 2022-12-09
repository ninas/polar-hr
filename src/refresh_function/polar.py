from peewee import fn
from playhouse.db_url import connect
from datetime import timedelta
from functools import cache, cached_property

from src.utils import gcp_utils, log
from src.db.sources import models as source_models
from src.db.workout import models as workout_models
from src.db.workout.workout import Workout

from src.polar_api.polar_api import PolarAPI


class Process:
    UNIX_SOCKET_PATH = "/cloudsql/"
    def __init__(self, logger):
        self.logger = logger

    @cache
    def database_connection_data(self, prefix):
        return [gcp_utils.fetch_config(f"{prefix}/db_name")], {
            "host": self.UNIX_SOCKET_PATH + gcp_utils.fetch_config(f"{prefix}/gcp_path"),
            "user": gcp_utils.fetch_config(f"{prefix}/username"),
            "password": gcp_utils.get_secret("db_workout"),
        }

    @cache
    def _connect_to_db(self, name, model):
        db_name, connection_info = self.database_connection_data(name)
        self.logger.debug(
            f"Opening connection to DB {name}",
            db={
                "name": db_name[0],
                "host": connection_info["host"],
                "user": connection_info["user"]
            }
        )
        model.database.init(db_name[0], **connection_info)
        model.database.connect()
        return model.database

    @cached_property
    def source_db(self):
        return self._connect_to_db("sources_db", source_models)


    @cached_property
    def workout_db(self):
        return self._connect_to_db("workout_db", workout_models)


    def get_sources(self, earliest):
        with self.source_db.atomic():
            results = (
                source_models.SourceInput.select()
                .where(source_models.SourceInput.created >= earliest)
                .execute()
            )
        return results


    def get_last_saved_workout_date(self):
        with self.workout_db.atomic():
            return workout_models.Workouts.select(
                fn.MAX(workout_models.Workouts.starttime)
            ).scalar()


    def map_data(self, data):
        # For each source, we want the workout where it was created after the start time, but before the start time of the next workout
        sources = self.get_sources(data[0].start_time)

        self.logger.info("Mapping workouts to sources",
                        workouts=[i.as_dict_for_logging() for i in data],
                        sources=[src.as_dict() for src in sources]
        )
        s_i = 0
        max_start = self.get_last_saved_workout_date()
        self.logger.info(f"Last saved workout: {max_start}")

        updated_workouts = []
        for workout in data:
            if max_start >= workout.start_time:
                continue
            added = False
            for i, source in enumerate(sources[s_i:]):
                if (
                    workout.start_time < source.created
                    and abs(source.created - workout.end_time) < timedelta(minutes=5)
                    and (
                        len(sources) == i + 1 or workout.start_time < sources[i + 1].created
                    )
                ):
                    workout.add_source(source)
                    updated_workouts.append(workout)
                    s_i = i + 1
                    added = True
                    self.logger.info(
                        "Found a match",
                        workout=workout.as_dict(),
                        source=source.as_dict(),
                    )
                    break

            if not added:
                self.logger.info("No match found", workout=workout.as_dict())

        return updated_workouts


    def save_to_db(self, workouts):
        for workout in workouts:
            w = Workout(self.workout_db, workout)
            w.insert_row()
