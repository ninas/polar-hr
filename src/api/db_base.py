import json
from functools import cache, cached_property
from datetime import datetime, timedelta
import isodate

from peewee import fn

from src.db.workout import models
from src.utils import log
from src.utils.db_utils import DBConnection
from src.api.complex_query import ComplexQuery


class DBBase:
    def __init__(self, db, logger=None, is_dev=False):
        self.db = db
        self.logger = logger
        if self.logger == None:
            self.logger = log.new_logger(is_dev=is_dev)
        self._is_dev = is_dev
        self.cq = ComplexQuery(self.logger, self._is_dev)

    def _fetch_from_model(self, model_select):
        model_to_func = {
            "SourcesMaterialized": self._basic_object,
            "WorkoutsMaterialized": self._basic_object,
            "Equipment": self._basic_object,
            "Tags": self._tags,
        }
        if model_select.model.__name__ not in model_to_func:
            return []
        return model_to_func[model_select.model.__name__](model_select)

    def _remove_none_lists(self, dicts):
        for i in dicts:
            for field_name, data in i.items():
                if isinstance(data, list) and len(data) == 1 and data[0] is None:
                    i[field_name] = []
        return dicts

    def _tags(self, model_select):
        with self.db.atomic():
            return [t.name for t in model_select]

    def _basic_object(self, model_select):
        with self.db.atomic():
            return self._remove_none_lists([m.json_friendly() for m in model_select])

    def query(self, model, query):
        model_select = self.cq.execute(query, model)
        self.logger.debug(
            "SQL Query", method="query", model=model.__name__, query=str(model_select)
        )

        if model_select is None:
            return {}
        return self._fetch_from_model(model_select)

    def by_id(self, model, identifiers):
        model_select = model.select()
        for field, ids in identifiers.items():
            model_select = model_select.orwhere(field << ids)

        self.logger.debug(
            "SQL Query", method="by_id", model=model.__name__, query=str(model_select)
        )

        return self._fetch_from_model(model_select)

    @cache
    def get_all(self, model):
        model_select = model.select().order_by(model.id)
        self.logger.debug(
            "SQL Query", method="get_all", model=model.__name__, query=str(model_select)
        )
        return self._fetch_from_model(model_select)
