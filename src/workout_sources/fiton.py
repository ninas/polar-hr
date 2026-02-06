import copy
import json
import re
from datetime import timedelta
from functools import cache, cached_property

import isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import override

import src.db.workout.models as models
from src.utils.gcp_utils import get_secret
from src.workout_sources.source_consts import SourceConsts
from src.workout_sources.video_source import VideoSource


class Fiton(VideoSource):
    BUCKET = "fiton_workout_info/fiton_workouts.json"

    @override
    def __init__(self, db, url, logger):
        super().__init__(db, url, logger)
        self.workout_id = url.split("/")[-1]

    @staticmethod
    @override
    def normalise_url(url):
        if url.startswith("fiton:"):
            url = url[6:]
        if url.isdigit():
            return f"https://app.fitonapp.com/browse/workout/{url}"
        return url

    @classmethod
    @cache
    def fetch_all_workout_data(cls):
        return json.loads(fetch_from_cloud_storage(Fiton.BUCKET))

    @classmethod
    @override
    def source_type(cls):
        return models.SourceType.FITON

    @cached_property
    @override
    def data(self):
        all_data = Fiton.fetch_all_workout_data()
        if self.workout_id not in all_data:
            raise Exception("Unknown Fiton workout")
        return all_data[self.workout_id]

    @property
    @override
    def title(self):
        return self.data["workoutName"]

    @property
    @override
    def creator(self):
        return f"{self.data['trainerName'].lower()}"

    @cached_property
    @override
    def duration(self):
        return timedelta(seconds=self.data["workoutData"]["part"]["continueTime"])

    @property
    @override
    def exercises(self):
        return []

    @override
    def _gen_tags(self):
        tags = super()._gen_tags()
        tags.update({"fiton"})
        for cat in self.data["workoutData"]["categoryList"]:
            tags.add(cat["categoryNameEN"])
        for equip in self.data["workoutData"]["equipments"]:
            if equip["nameEN"] == "mat":
                continue
            tags.add(equip["nameEN"])
        return tags
