import abc
from functools import cached_property

from overrides import EnforceOverrides

import src.db.workout.models as models
from src.db.workout.workout_data_store import WorkoutDataStore
from src.utils import log


class DBInterface(EnforceOverrides, abc.ABC):
    def __init__(self, db, logger=None):
        self.db = db
        self.model = None
        if logger is None:
            logger = log.new_logger()

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
                    self.logger.info(
                        f"New tag: {i.name}", tag_name=i.name, action="new"
                    )
        return all_models
