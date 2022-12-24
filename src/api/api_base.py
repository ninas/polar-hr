import json
from functools import cache

from peewee import prefetch, fn

from src.db.workout import models
from src.utils import log
from src.utils.db_utils import DBConnection


class APIBase:
    PREFETCH_MAPPINGS = {
        models.Workouts: {
            models.Tags: {"through": models.Workouts.tags.get_through_model(),},
            models.Sources: {"through": models.Workouts.sources.get_through_model(),},
            models.Equipment: {
                "through": models.Workouts.equipment.get_through_model(),
            },
            models.HRZones: {"flip": True},
            models.Samples: {"flip": True},
        },
        models.Sources: {
            models.Workouts: {"through": models.Workouts.sources.get_through_model()},
            models.Tags: {"through": models.Sources.tags.get_through_model()},
        },
        models.Tags: {},
        models.Equipment: {},
    }

    def __init__(self, logger=None):
        self.logger = logger
        if self.logger == None:
            self.logger = log.new_logger(is_dev=True)

        self._models = {}
        self.db = self._get_db()

    @classmethod
    @cache
    def _get_db(cls):
        logger = log.new_logger(is_dev=True)
        return DBConnection(logger).workout_db

    def _lazy_load_model(self, model):
        return self._models.setdefault(model, model.select())

    @cache
    def _prefetch(self, main_model):
        with self.db.atomic():
            mm = self._lazy_load_model(main_model)
            for second_model, options in self.PREFETCH_MAPPINGS[main_model].items():

                sm = self._lazy_load_model(second_model)

                modelselects = [mm, sm] if "flip" not in options else [sm, mm]

                if "through" in options:
                    tm = self._lazy_load_model(options["through"])
                    modelselects.insert(1, tm)
                prefetch(*modelselects)
            return mm

    @cache
    def prefetch_workouts(self):
        return self._prefetch(models.Workouts)

    @cache
    def prefetch_sources(self):
        return self._prefetch(models.Sources)

    @cache
    def prefetch_all(self):
        return {
            "workouts": self.prefetch_workouts(),
            "sources": self.prefetch_sources(),
        }

    def fetch_from_model(self, model_type, model=None):
        model_to_func = {
            "Sources": self._sources,
            "Workouts": self._workouts,
            "Equipment": self._basic_object,
            "Tags": self._basic_object,
        }
        if model_type not in model_to_func:
            return []
        if model is None:
            model = self._prefetch(getattr(models, model_type))
        return model_to_func[model_type](model)

    @cache
    def _sources(self, sources_model_select):
        data = {}
        with self.db.atomic():
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
            for workout in workouts_model_select:
                w = workout.json_friendly()
                w["sources"] = [s.url for s in workout.sources]
                w["equipment"] = [e.json_friendly() for e in workout.equipment]
                w["tags"] = [t.name for t in workout.tags]
                w["hrzones"] = {}
                data[workout.id] = w

            for sample in self._lazy_load_model(models.Samples):
                data[sample.workout.id]["samples"] = sample.samples

            for zone in self._lazy_load_model(models.HRZones):
                z = zone.json_friendly()
                del z["workout"]
                data[zone.workout.id]["hrzones"][zone.zonetype] = z

        return data

    @cache
    def _basic_object(self, model_select):
        with self.db.atomic():
            return [m for m in model_select.dicts()]

    def by_id(self, model, identifiers):
        name = model.__name__
        model_select = self._prefetch(model)
        for field, ids in identifiers.items():
            model_select.where(field << ids)

        return self.fetch_from_model(name, model_select)
