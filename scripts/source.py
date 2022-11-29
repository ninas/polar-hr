import math

from db import models
from .utils import youtube_vid_id
from overrides import override

from .db_interface import DBInterface


class Source(DBInterface):
    @override
    def __init__(self, db, url, data):
        super().__init__(db, data)
        self.url = Source.normalise_url(url)
        self._tags = None
        self._exercises = None
        self._tags = None

    @staticmethod
    def normalise_url(url):
        if Source.get_source_type(url) == models.SourceType.YOUTUBE:
            vid_id = youtube_vid_id(url)
            return f"https://www.youtu.be/{vid_id}"
        return url

    @staticmethod
    def get_source_type(url):
        if "youtu" in url:
            return models.SourceType.YOUTUBE
        return models.SourceType.UNKNOWN

    @staticmethod
    def load_source(db, url):
        url = Source.normalise_url(url)

        # Check whether it's already in the db first
        res = Source._find(db, models.Sources, models.Sources.url, url)
        if res is not None:
            return ExistingSource(db, url, res)

        if Source.get_source_type(url) == models.SourceType.YOUTUBE:
            from .youtube import Youtube

            return Youtube.load_source(db, url)
        print("Unknown source")
        return UnknownSource(db, url)

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
        if self._tags is not None:
            return self._tags
        self._tags = set()
        if self.duration is not None:
            self._tags.add(self._gen_tag_from_duration())
        return self._tags

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
            all_tags.update(set(
                self._insert_tags([self.creator], models.TagType.CREATOR)
            ))

        if len(self.exercises) > 0:
            print("Gonna insert exercises")

            all_tags.update(set(
                self._insert_tags(self.exercises, models.TagType.EXERCISE)
            ))

        if len(self.tags) > 0:
            print("Gonna insert tags")
            all_tags.update(set(
                self._insert_tags(self.tags, models.TagType.TAG)
            ))

        with self.db.atomic():
            self.model = models.Sources.create(
                url=self.url,
                sourcetype=self.source_type,
                name=self.title,
                length=self.duration,
                extra_info=self.extra_info,
                creator=self.creator,
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
    def __init__(self, db, url):
        super().__init__(db, url, {})


class ExistingSource(Source):
    @override
    def __init__(self, db, url, model):
        super().__init__(db, url, None)
        self.model = model

    @override
    def insert_row(self):
        pass
