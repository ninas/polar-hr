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
        return []

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
        with self.db.atomic():
            self.model = models.Sources.create(
                url=self.url,
                sourcetype=self.source_type,
                name=self.title,
                creator=self.creator,
                length=self.duration,
                extra_info=self.extra_info,
            )

            if len(self.tags) > 0:
                print("Gonna insert tags")
                self.model.tags.add(
                    self._insert_basic_model_data(self.tags, models.Tags)
                )
            if len(self.exercises) > 0:
                print("Gonna insert exercises")
                self.model.exercises.add(
                    self._insert_basic_model_data(self.exercises, models.Exercises)
                )

            self.model.save()

        return self.model

    def _insert_basic_model_data(self, data, type_model):
        insert_data = [{"name": val} for val in data]
        with self.db.atomic():
            inserts = type_model.insert_many(insert_data).on_conflict_ignore().execute()

        all_models = [type_model.get(type_model.name == i["name"]) for i in insert_data]
        if inserts is not None:
            new_inserts = set(i[0] for i in inserts)
            for i in all_models:
                if i.id in new_inserts:
                    print("New:", i.name)
        return all_models


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
