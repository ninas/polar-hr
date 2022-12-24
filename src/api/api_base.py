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
    }

    def __init__(self, logger=None):
        self.logger = logger
        if self.logger == None:
            self.logger = log.new_logger(is_dev=True)

        self.db = DBConnection(logger).workout_db
        self._models = {}

    def _lazy_load_model(self, model):
        return self._models.setdefault(model, model.select())

    def _prefetch(self, main_model):
        with self.db.atomic():
            mm = self._lazy_load_model(main_model)
            for second_model, options in self.PREFETCH_MAPPINGS[main_model].items():

                sm = self._lazy_load_model(second_model)

                models = [mm, sm] if "flip" not in options else [sm, mm]

                if "through" in options:
                    tm = self._lazy_load_model(options["through"])
                    models.insert(1, tm)
                prefetch(*models)
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

    @cache
    def sources(self, sources_model=None):
        if sources_model is None:
            sources_model = self.prefetch_sources()
        data = {}
        with self.db.atomic():
            for source in sources_model:
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
    def workouts(self):
        workouts = self.prefetch_workouts()
        data = {}
        with self.db.atomic():
            for workout in workouts:
                w = workout.json_friendly()
                w["sources"] = [s for s in workout.sources]
                w["equipment"] = [e for e in workout.equipment]
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

    def tags(self):
        with self.db.atomic():
            return [t for t in self._lazy_load_model(models.Tags).dicts()]

    def equipment(self):
        with self.db.atomic():
            return [e for e in self._lazy_load_model(models.Equipment).dicts()]

