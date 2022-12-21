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
        return UnknownSource

    @staticmethod
    def load_source(db, url, logger=None):
        url = Source.normalise_url(url)

        # Check whether it's already in the db first
        res = Source._find(db, models.Sources, models.Sources.url, url)
        if res is not None:
            return ExistingSource(db, url, res, logger)

        source_obj = Source.get_source_type(url)
        # __dict__ doesn't include inherited attrs
        if "load_source" in source_obj.__dict__:
            return source_obj.load_source(db, url, logger)
        return source_obj(db, url, logger)

            return Youtube.load_source(db, url, logger)
        return UnknownSource(db, url, logger)

    @property
    def title(self):
        return None

    @property
    def duration(self):
        return None

    @property
    def extra_info(self):
        return None

    @property
    def tags(self):
        tags = set()
        if self.duration is not None:
            tags.add(self._gen_tag_from_duration())
        return tags

    @property
    def exercises(self):
        return []

    @property
    def creator(self):
        return None

    @property
    def source_type(self):
        return models.SourceType.UNKNOWN

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

    def _gen_tag_from_duration(self):
        in_mins = self.duration.total_seconds() / 60
        start = int(in_mins / 10) * 10
        end = math.ceil(in_mins / 10) * 10
        if start == end:
            end += 10
        return f"{start}-{end}min"


class UnknownSource(Source):
    def __init__(self, db, url, logger=None):
        super().__init__(db, url, {}, logger)


class ExistingSource(Source):
    @override
    def __init__(self, db, url, model, logger):
        super().__init__(db, url, logger)
        self.model = model

    @override
    def insert_row(self):
        pass
