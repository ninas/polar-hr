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
    PAGINATION_STEP = 25

    def __init__(self, db, logger=None, is_dev=False):
        self.db = db
        self.logger = logger
        if self.logger == None:
            self.logger = log.new_logger(is_dev=is_dev)
        self._is_dev = is_dev
        self.cq = ComplexQuery(self.logger, self._is_dev)

    def _fetch_from_model(self, model_select, pagination_id):
        model_to_func = {
            "SourcesMaterialized": self._paginated_object,
            "WorkoutsMaterialized": self._paginated_object,
            "Equipment": self._basic_object,
            "Tags": self._tags,
        }
        if model_select.model.__name__ not in model_to_func:
            return {"data": [], "nextPage": -1}
        if pagination_id is not None:
            model_select = model_select.order_by(model_select.model.id).paginate(
                pagination_id, self.PAGINATION_STEP
            )
        return model_to_func[model_select.model.__name__](model_select, pagination_id)

    def _remove_none_lists(self, dicts):
        for i in dicts:
            for field_name, data in i.items():
                if isinstance(data, list) and len(data) == 1 and data[0] is None:
                    i[field_name] = []
        return dicts

    def _tags(self, model_select, pagination_id):
        with self.db.atomic():
            return self._pag_result([t.name for t in model_select])

    def _basic_object(self, model_select, pagination_id):
        with self.db.atomic():
            return self._pag_result([m.json_friendly() for m in model_select])

    def _paginated_object(self, model_select, pagination_id):
        with self.db.atomic():
            data = self._remove_none_lists([m.json_friendly() for m in model_select])
        results = {}
        if pagination_id is not None and len(data) == self.PAGINATION_STEP:
            pagination_id += 1
        else:
            pagination_id = -1
        return self._pag_result(data, pagination_id)

    def _pag_result(self, data, next_page=-1):
        return {
            "nextPage": next_page,
            "data": data,
        }

    def query(self, model, query, pagination_id=None):
        model_select = self.cq.execute(query, model)
        self.logger.debug(
            "SQL Query", method="query", model=model.__name__, query=str(model_select)
        )

        if model_select is None:
            return {}
        return self._fetch_from_model(model_select, pagination_id)

    def by_id(self, model, identifiers, pagination_id=None):
        model_select = model.select()
        for field, ids in identifiers.items():
            model_select = model_select.orwhere(field << ids)

        self.logger.debug(
            "SQL Query", method="by_id", model=model.__name__, query=str(model_select)
        )

        return self._fetch_from_model(model_select, pagination_id)

    @cache
    def get_all(self, model, pagination_id=None):
        model_select = model.select().order_by(model.id)
        self.logger.debug(
            "SQL Query", method="get_all", model=model.__name__, query=str(model_select)
        )
        return self._fetch_from_model(model_select, pagination_id)
