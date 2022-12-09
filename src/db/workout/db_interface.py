from overrides import EnforceOverrides
import abc
from functools import cached_property
import structlog

import src.db.workout.models as models
from src.db.workout.workout_data_store import WorkoutDataStore


class DBInterface(EnforceOverrides, abc.ABC):
    def __init__(self, db, data, logger=None):
        self.db = db
        self._data = data
        self.model = None
        if logger is None:
            logger = structlog.get_logger()
        if isinstance(self._data, WorkoutDataStore):
            self.logger = logger.bind(
                workout = self._data.log_abridged()
            )

    @cached_property
    def data(self):
        return self._data

    @abc.abstractmethod
    def insert_row(self):
        pass

    @staticmethod
    def _find(db, model, field, val):
        try:
            with db.atomic():
                return model.get(field == val)
        except model.DoesNotExist:
            pass
        return None

    def _insert_tags(self, data, type_data):
        self.logger.debug("Inserting tag data", tag_type=type_data, tags=data)
        insert_data = [{"name": val, "tagtype": type_data} for val in data]
        with self.db.atomic():
            inserts = (
                models.Tags.insert_many(insert_data).on_conflict_ignore().execute()
            )

            all_models = models.Tags.select().where(models.Tags.name << data).execute()
        if inserts is not None and len(inserts) > 0:
            new_inserts = set(i[0] for i in inserts)
            for i in sorted(all_models, key=lambda x: x.name):
                if i.id in new_inserts:
                    self.logger.info(f"New tag: {i.name}", tag_name=i.name, action="new")
        return all_models
