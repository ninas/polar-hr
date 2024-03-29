from datetime import timedelta

from peewee import fn

from src.db.sources import models as source_models
from src.db.workout import models as workout_models
from src.db.workout.workout import Workout
from src.utils.db_utils import DBConnection


class ProcessData:
    UNIX_SOCKET_PATH = "/cloudsql/"

    def __init__(self, logger):
        self.logger = logger
        self.db = DBConnection(self.logger)

    def get_sources(self, earliest):
        with self.db.source_db.atomic():
            results = (
                source_models.SourceInput.select()
                .where(source_models.SourceInput.created >= earliest)
                .order_by(source_models.SourceInput.created)
                .execute()
            )
        return results

    def get_last_saved_workout_date(self):
        with self.db.workout_db.atomic():
            return workout_models.Workouts.select(
                fn.MAX(workout_models.Workouts.starttime)
            ).scalar()

    def map_data(self, data):
        # For each source, we want the workout where it was created after the start time, but before the start time of the next workout
        sources = self.get_sources(data[0].start_time)

        self.logger.info(
            "Mapping workouts to sources",
            workouts=[i.log_abridged() for i in data],
            sources=[src.as_dict() for src in sources],
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
                        len(sources) == i + 1
                        or workout.start_time < sources[i + 1].created
                    )
                ):
                    workout.add_source(source)
                    updated_workouts.append(workout)
                    s_i = i + 1
                    added = True
                    self.logger.info(
                        "Found a match",
                        workout=workout.log_abridged(),
                        source=source.as_dict(),
                    )
                    break

            if not added:
                self.logger.info("No match found", workout=workout.log_abridged())

        return updated_workouts

    def save_to_db(self, workouts):
        for workout in workouts:
            w = Workout(self.db.workout_db, workout, self.logger)
            w.insert_row()
            workout_models.refresh_materialized_views()
