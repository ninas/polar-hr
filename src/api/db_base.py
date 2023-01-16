import json
from functools import cache, cached_property
from datetime import datetime, timedelta
import isodate

from peewee import prefetch, fn

from src.db.workout import models
from src.utils import log
from src.utils.db_utils import DBConnection
from src.api.complex_query import ComplexQuery


class DBBase:
    PREFETCH_MAPPINGS = {
        models.Workouts: {
            models.Tags: models.Workouts.tags.get_through_model(),
            models.Sources: models.Workouts.sources.get_through_model(),
            models.Equipment: models.Workouts.equipment.get_through_model(),
        },
        models.Sources: {
            models.Workouts: models.Workouts.sources.get_through_model(),
            models.Tags: models.Sources.tags.get_through_model(),
        },
        models.Tags: {},
        models.Equipment: {},
        models.HRZones: {models.Workouts: None},
        models.Samples: {models.Workouts: None},
    }

    def __init__(self, db, logger=None, is_dev=False):
        self.db = db
        self.logger = logger
        if self.logger == None:
            self.logger = log.new_logger(is_dev=is_dev)
        self._is_dev = is_dev

    @cache
    def _prefetch(self, main_model_select):
        with self.db.atomic():
            if main_model_select is None:
                main_model_select = main_model.select()
            mm = main_model_select
            for second_model, through in self.PREFETCH_MAPPINGS[
                main_model_select.model
            ].items():

                sm = second_model.select()
                self._prefetch_models(main_model_select, sm, through)

            return main_model_select

    @cache
    def _prefetch_models(self, mod1, mod2, through=None):
        modelselects = [mod1, mod2]

        if through is not None:
            modelselects.insert(1, through.select())
        prefetch(*modelselects)

    def _fetch_from_model(self, model_select):
        model_to_func = {
            "Sources": self._sources,
            "Workouts": self._workouts,
            "Equipment": self._basic_object,
            "Tags": self._tags,
        }
        if model_select.model.__name__ not in model_to_func:
            return []
        return model_to_func[model_select.model.__name__](model_select)

    @cache
    def _sources(self, sources_model_select):
        data = {}
        with self.db.atomic():
            sources_model_select = self._prefetch(sources_model_select)
            for source in sources_model_select:
                s = source.json_friendly()
                s["tags"] = []
                s["exercises"] = []
                for t in source.tags:
                    if t.tagtype == models.TagType.EXERCISE:
                        s["exercises"].append(t.name)
                    elif (
                        t.tagtype == models.TagType.TAG
                        or t.tagtype == models.TagType.SPORT
                    ):
                        s["tags"].append(t.name)
                s["workouts"] = [w.id for w in source.workouts]
                data[source.id] = s
        return data

    @cache
    def _workouts(self, workouts_model_select):
        data = {}
        with self.db.atomic():
            workouts_model_select = self._prefetch(workouts_model_select)
            for workout in workouts_model_select:
                w = workout.json_friendly()
                w["sources"] = [s.url for s in workout.sources]
                w["equipment"] = [e.json_friendly() for e in workout.equipment]
                w["tags"] = [t.name for t in workout.tags]
                data[workout.id] = w

        return data

    @cache
    def _tags(self, model_select):
        with self.db.atomic():
            return [t.name for t in model_select]

    @cache
    def _basic_object(self, model_select):
        with self.db.atomic():
            return [m for m in model_select.dicts()]

    def query(self, model, query):
        cq = ComplexQuery(query, model, self.logger, self._is_dev)
        model_select = cq.execute()
        self.logger.debug(
            "SQL Query", method="query", model=model.__name__, query=model_select
        )

        if model_select is None:
            return {}
        return self._fetch_from_model(model_select)

    def by_id(self, model, identifiers):
        model_select = model.select()
        for field, ids in identifiers.items():
            model_select = model_select.orwhere(field << ids)

        self.logger.debug(
            "SQL Query", method="by_id", model=model.__name__, query=model_select
        )

        return self._fetch_from_model(model_select)

    def get_all(self, model):
        model_select = model.select()
        self.logger.debug(
            "SQL Query", method="get_all", model=model.__name__, query=model_select
        )
        return self._fetch_from_model(model_select)
