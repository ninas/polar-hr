import json
from functools import cache, cached_property
import isodate

from peewee import prefetch, fn

from src.db.workout import models
from src.utils import log
from src.utils.db_utils import DBConnection


class APIBase:
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

    def __init__(self, logger=None, is_dev=True):
        self.logger = logger
        if self.logger == None:
            self.logger = log.new_logger(is_dev=is_dev)

        if is_dev:
            import logging

            logger = logging.getLogger("peewee")
            logger.addHandler(logging.StreamHandler())
            logger.setLevel(logging.DEBUG)
        self._models = {}
        self.db = self._get_db()

    @classmethod
    @cache
    def _get_db(cls):
        logger = log.new_logger(is_dev=True)
        return DBConnection(logger).workout_db

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
            "Tags": self._basic_object,
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
                w["hrzones"] = {}
                data[workout.id] = w

                sample_model = models.Samples.select()
                self._prefetch_models(sample_model, workouts_model_select)
                for sample in sample_model:
                    data[sample.workout_id]["samples"] = sample.samples

            hr_model = models.HRZones.select()
            self._prefetch_models(hr_model, workouts_model_select)
            for zone in hr_model:
                z = zone.json_friendly()
                del z["workout"]
                data[zone.workout_id]["hrzones"][zone.zonetype] = z

        return data

    @cache
    def _basic_object(self, model_select):
        with self.db.atomic():
            return [m for m in model_select.dicts()]

    def _gen_sources_query(self, query):
        srcs = models.Sources.select(models.Sources.id)
        source_tags_to_filter = set()

        if query.exercises is not None:
            source_tags_to_filter.update(set(query.exercises))
        if query.tags is not None:
            source_tags_to_filter.update(set(query.tags))

        if len(source_tags_to_filter) > 0:
            sub_query = (
                models.Sources.select(models.Sources.id)
                .join(models.Sources.tags.get_through_model())
                .join(models.Tags)
                .where(models.Tags.name << source_tags_to_filter)
                .group_by(models.Sources.id)
                .having(fn.COUNT(models.Sources.id) == len(source_tags_to_filter))
            )
            srcs = srcs.where(models.Sources.id << sub_query)

        if query.creator is not None:
            srcs = srcs.where(models.Sources.creator == query.creator)

        if query.length_min is not None:
            srcs = srcs.where(
                models.Sources.length >= timedelta(seconds=query.length_min)
            )
        if query.length_max is not None:
            srcs = srcs.where(models.Sources.length <= timedelta(query.length_max))

        if query.source_type is not None:
            srcs = srcs.where(models.Sources.sourcettype == query.source_type)

        return srcs

    def query_sources(self, query):
        return_data = {}
        if query.source_attributes is not None:
            srcs = self._gen_sources_query(query.source_attributes)
            )
        return return_data

    def by_id(self, model, identifiers):
        model_select = model.select()
        for field, ids in identifiers.items():
            model_select = model_select.orwhere(field << ids)

        return self._fetch_from_model(model_select)

    def get_all(self, model):
        return self._fetch_from_model(model.select())
