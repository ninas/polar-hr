import copy
import re
from functools import cache, cached_property

import isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from overrides import override

import src.db.workout.models as models
from src.workout_sources.video_source import VideoSource
from src.workout_sources.source_consts import SourceConsts
from src.utils.gcp_utils import get_secret


class Youtube(VideoSource):
    def __init__(self, db, url, data, logger):
        super().__init__(db, url, logger)
        self._data = data

    @staticmethod
    @override
    def load_source(db, url, logger):
        url = Youtube.normalise_url(url)
        data = Youtube.get_data(url)
        if data["snippet"]["channelTitle"].lower() == "heather robertson":
            return HeatherRobertsonYoutube(db, url, data, logger)
        return Youtube(db, url, data, logger)

    @staticmethod
    @override
    def normalise_url(url):
        vid_id = Youtube.youtube_vid_id(url)
        return f"https://www.youtu.be/{vid_id}"

    @staticmethod
    @cache
    def youtube_vid_id(url):
        m = SourceConsts.id_regex.match(url)
        if m is None:
            raise Exception(f"Unable to find id in url: {url}")
        return m.group(1).strip()

    @classmethod
    @cache
    def api_key():
        return get_secret("youtube_api_key")

    @staticmethod
    @cache
    def get_data(url):
        # https://www.googleapis.com/youtube/v3/videos?id=Mvo2snJGhtM&key=<key>&part=snippet,contentDetails
        secret = Youtube.api_key()
        youtube_client = build("youtube", "v3", developerKey=secret)

        vid_id = Youtube.youtube_vid_id(url)
        results = (
            youtube_client.videos()
            .list(part="snippet,contentDetails", id=vid_id)
            .execute()
        )

        if len(results["items"]) != 1:
            raise Exception(
                f"Unexpectedly shaped youtube data object: {url} : {vid_id} \n {results}"
            )

        return results["items"][0]

    @classmethod
    @property
    def source_type(cls):
        return models.SourceType.YOUTUBE

    @cached_property
    def data(self):
        return self._data

    @property
    @override
    def title(self):
        return self.data["snippet"]["title"]

    @property
    @override
    def creator(self):
        return self.data["snippet"]["channelTitle"].lower()

    @cached_property
    @override(check_signature=False)
    def duration(self):
        return isodate.parse_duration(self.data["contentDetails"]["duration"])

    @cached_property
    @override(check_signature=False)
    def exercises(self):

        description = self.data["snippet"]["description"].lower()

        exercises = set()

        for i in description.split("\n"):
            m = SourceConsts.chapters_regex.match(i)
            if m is None:
                continue
            cleaned = Youtube._clean_exercise(m.group(2)).strip()
            if len(cleaned) > 3:
                exercises.add(cleaned)
        return exercises

    @override
    def _gen_tags(self):
        tags = super()._gen_tags()
        tags.update(self.data["snippet"]["tags"])
        tags.update(self._add_from_text(self.data["snippet"]["description"]))
        return tags

    @classmethod
    @cache
    def _clean_exercise(cls, val):
        # remove extra words
        for e in SourceConsts.exercises_strip:
            val = re.sub(r"(" + e + r")\b", "", val)

        # standardise names (but only if they're not in the middle of a word"
        for k, v in SourceConsts.exercise_dupes.items():
            val = re.sub(r"(" + k + r")\b", v, val)

        # standardise on the plural form
        for e in SourceConsts.exercise_plurals:
            val = re.sub(r"(" + e + r")\b", f"{e}s", val)

        # remove any bracketed extra info - i.e. (L) or (R)
        val = re.sub("\(.+\)", "", val)
        # remove any frequencies - i.e. x3
        val = re.sub(" x[0-9]", "", val)
        # make sure we start with the exercise, i.e. remove bulletpoints (-, *, etc)
        val = re.sub("^\W+", "", val)
        # standardise on '+' instead of '&' in descriptions
        val = val.replace("&", "+")

        return val.strip()


class HeatherRobertsonYoutube(Youtube):
    @cached_property
    @override(check_signature=False)
    def exercises(self):
        description = self.data["snippet"]["description"].lower()

        exercises = set()
        start = None
        for option in ["workout breakdown", "intro", "warm up"]:
            start = self._get_start_of_exercise_list(option)
            if start is not None:
                break
        if start is None:
            return exercises

        des = description[start:].split("\n")

        i = 0

        while i < len(des):
            if (
                len(des[i]) == 0
                or "rest" in des[i]
                or "intro" in des[i]
                or "warm up" in des[i]
                or len(des[i]) == 0
            ):
                i += 1
                continue
            elif (
                "cool down" in des[i]
                or len(des[i]) > 60
                or "equipment needed" in des[i]
            ):
                break

            res = SourceConsts.chapters_regex.match(des[i])
            val = res.group(2).strip() if res is not None else des[i]
            if val.startswith("circuit") or val.startswith("superset"):
                i += 1
                continue

            val = HeatherRobertsonYoutube._clean_exercise(val)
            if len(val) > 3:
                exercises.add(val)

            i += 1

        return exercises

    @override
    def _gen_tags(self):
        tags = super()._gen_tags()
        tags.update(self._hiit_intervals())
        return tags

    def _hiit_intervals(self):
        # e.g. 40s work + 20s rest
        on_off = re.compile("(\d{2}s.+\d{2}s rest)")
        res = on_off.search(self.data["snippet"]["description"])
        if res is None:
            return set()

        result = res.group(1)
        result = result.replace(" of", "")
        result = result.replace("workout", "work")
        if len(res.group(1)) > 20:
            result = result[:20]
        return {result.strip()}

    def _get_start_of_exercise_list(self, wu):
        description = self.data["snippet"]["description"].lower()
        loc = description.find(wu)
        if loc < 0:
            return None
        return description.find("\n", loc)
