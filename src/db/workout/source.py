import math
from functools import cache, cached_property

from overrides import override

import src.db.workout.models as models
from src.db.workout.db_interface import DBInterface


class Source(DBInterface):
    @override
    def __init__(self, db, url, logger=None):
        super().__init__(db, logger)
        self.url = Source.normalise_url(url)
        self.logger = logger.bind(url=self.url, source_type=self.__class__.__name__)

    @staticmethod
    def normalise_url(url):
        source_obj = Source.get_source_type(url)
        return source_obj.normalise_url(url)

    @staticmethod
    def get_source_type(url):
        if "youtu" in url:
            from src.workout_sources.youtube import Youtube

            return Youtube
        if "fiton" in url:
            from src.workout_sources.fiton import Fiton

            return Fiton
        return UnknownSource

    @staticmethod
    def load_source(db, url, logger=None):
        url = Source.normalise_url(url)

        # Check whether it's already in the db first
        res = Source.find(db, models.Sources, models.Sources.url, url)
        if res is not None:
            return ExistingSource(db, url, res, logger)

        source_obj = Source.get_source_type(url)
        # __dict__ doesn't include inherited attrs
        if "load_source" in source_obj.__dict__:
            return source_obj.load_source(db, url, logger)
        return source_obj(db, url, logger)

    def _model_val(self, field, default=None):
        if self.model is not None:
            return getattr(self.model, field)
        return default

    @property
    def data(self):
        return None

    @property
    def title(self):
        return self._model_val("name")

    @property
    def duration(self):
        return self._model_val("length")

    @property
    def extra_info(self):
        return self._model_val("extrainfo")

    @property
    def tags(self):
        return self._model_val("tags", [])

    @property
    def exercises(self):
        exercises = []
        for val in self.tags:
            if val.tagtype == models.TagType.EXERCISE:
                exercises.append(val.name)
        return exercises

    @property
    def creator(self):
        return self._model_val("creator")

    @classmethod
    @property
    def source_type(cls):
        return None

    @override
    def insert_row(self):
        all_tags = set()
        if self.creator:
            all_tags.update(
                set(self._insert_tags([self.creator], models.TagType.CREATOR))
            )

        if len(self.exercises) > 0:
            all_tags.update(
                set(self._insert_tags(self.exercises, models.TagType.EXERCISE))
            )

        if len(self.tags) > 0:
            all_tags.update(set(self._insert_tags(self.tags, models.TagType.TAG)))

        with self.db.atomic():
            self.model = models.Sources.create(
                url=self.url,
                sourcetype=self.source_type,
                name=self.title,
                length=self.duration,
                creator=self.creator,
                extra_info=self.extra_info,
            )
            self.model.tags.add(list(all_tags))
            self.model.save()

        return self.model


class UnknownSource(Source):
    @staticmethod
    @override
    def normalise_url(url):
        return url

    @classmethod
    @property
    def source_type(cls):
        return models.SourceType.UNKNOWN


class ExistingSource(Source):
    @override
    def __init__(self, db, url, model, logger):
        super().__init__(db, url, logger)
        self.model = model

    @staticmethod
    @override
    def normalise_url(url):
        return url

    @override
    def insert_row(self):
        return self.model

    @property
    def source_type(cls):
        return cls.model.sourcetype
