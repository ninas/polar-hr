import re, copy, math, isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from overrides import override

from .utils import get_secret, youtube_vid_id
from .youtube_consts import YTConsts
from db import models
from .source import Source


class Youtube(Source):
    _secret = None

    @staticmethod
    @override
    def load_source(db, url):
        url = Youtube.normalise_url(url)
        data = Youtube.get_data(url)
        if data["snippet"]["channelTitle"].lower() == "heather robertson":
            return HeatherRobertsonYoutube(db, url, data)
        return Youtube(db, url, data)

    @staticmethod
    def api_key():
        if Youtube._secret is not None:
            return Youtube._secret
        Youtube._secret = get_secret("youtube_api_key")
        return Youtube._secret

    @staticmethod
    def get_data(url):
        # https://www.googleapis.com/youtube/v3/videos?id=Mvo2snJGhtM&key=<key>&part=snippet,contentDetails
        secret = Youtube.api_key()
        youtube_client = build("youtube", "v3", developerKey=secret)

        vid_id = youtube_vid_id(url)
        try:
            results = (
                youtube_client.videos()
                .list(part="snippet,contentDetails", id=vid_id)
                .execute()
            )
        except HttpError as e:
            print(f"A HTTP error {e.resp.status} occurred:\n{e.content}")
            return None

        if len(results["items"]) != 1:
            raise Exception(
                f"Unexpectedly shaped youtube data object: {url} : {vid_id} \n {results}"
            )

        return results["items"][0]

    @property
    @override
    def source_type(self):
        return models.SourceType.YOUTUBE

    @property
    @override
    def data(self):
        if self._data is not None:
            return self._data
        self._data = Youtube.get_data(self.url)
        return self._data

    @property
    @override
    def tags(self):
        if self._tags is not None:
            return self._tags

        tags = super().tags
        strip_words = sorted(
            list(copy.deepcopy(YTConsts.strip_words)), key=len, reverse=True
        )

        for i in sorted(self.data["snippet"]["tags"], key=len):
            i = i.lower()

            if i in YTConsts.ignore_tags:
                continue

            if i in YTConsts.dedupes:
                i = YTConsts.dedupes[i]
            else:
                i = self._strip_words(strip_words, i)
                i = self._remove_helper_words(i)

            if i in YTConsts.ignore_tags:
                continue

            if len(i) >= 3:
                tags.add(i)
                strip_words.append(i)
                if len(i.split(" ")) == 1 and i[-1] == "s":
                    strip_words.append(i[:-1])
                strip_words = sorted(strip_words, key=len, reverse=True)

        self._tags = self._enrich_tags(tags)

        return self._tags

    @property
    @override
    def title(self):
        return self.data["snippet"]["title"]

    @property
    @override
    def creator(self):
        return self.data["snippet"]["channelTitle"].lower()

    @property
    @override
    def duration(self):
        return isodate.parse_duration(self.data["contentDetails"]["duration"])

    @property
    @override
    def exercises(self):
        if self._exercises is not None:
            return self._exercises

        description = self.data["snippet"]["description"].lower()

        self._exercises = set()

        for i in description.split("\n"):
            m = YTConsts.chapters_regex.match(i)
            if m is None:
                continue
            cleaned = self._clean_exercise(m.group(2)).strip()
            if len(cleaned) > 3:
                self._exercises.add(cleaned)
        return self._exercises

    def _strip_words(self, words, val):
        for j in words:
            val = re.sub(r"\b" + j + r"\b", "", val)
            val = re.sub(r"\s+", " ", val)
        return val.strip()

    def _remove_helper_words(self, i):
        for t in ["s", "and", "with", "for", ","]:
            if i.startswith(f"{t} "):
                i = i[len(t) :]
            if i.endswith(f" {t}"):
                i = i[: -len(t)]
            i = i.strip()
        return i

    def _add_from_description(self):
        tags = set()
        for i in YTConsts.possible_tags:
            if i in tags:
                continue
            elif (
                i in self.data["snippet"]["title"]
                or i in self.data["snippet"]["description"]
            ):
                tags.add(i)
        return tags

    def _semantically_update(self, tags):
        to_remove = set()
        to_add = set()
        for tag in tags:
            if tag in YTConsts.expands:
                to_add.update(YTConsts.expands[tag])
                to_remove.add(tag)
            if tag in YTConsts.dedupes:
                to_add.add(YTConsts.dedupes[tag])
                to_remove.add(tag)
            if tag.startswith("no ") and tag[3:] in tags:
                to_remove.add(tag[3:])
            if tag.endswith("s") and tag[:-1] in tags:
                to_remove.add(tag[:-1])

        if "no equipment" in tags:
            to_remove.add("weights")

        for k, v in YTConsts.mappings.items():
            if k in tags and v not in tags:
                to_add.add(v)

        tags.update(to_add)
        tags = tags - to_remove
        return tags

    def _enrich_tags(self, tags):
        tags.update(self._add_from_description())

        for r in range(2):
            tags = self._semantically_update(tags)

        return tags

    def _clean_exercise(self, val):
        # remove extra words
        for e in YTConsts.exercises_strip:
            val = re.sub(r"(" + e + r")\b", "", val)

        # standardise names (but only if they're not in the middle of a word"
        for k, v in YTConsts.exercise_dupes.items():
            val = re.sub(r"(" + k + r")\b", v, val)

        # standardise on the plural form
        for e in YTConsts.exercise_plurals:
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
    @property
    @override
    def exercises(self):
        if self._exercises is not None:
            return self._exercises

        description = self.data["snippet"]["description"].lower()

        self._exercises = set()
        start = None
        for option in ["workout breakdown", "intro", "warm up"]:
            start = self._get_start_of_exercise_list(option)
            if start is not None:
                break
        if start is None:
            return self._exercises

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

            res = YTConsts.chapters_regex.match(des[i])
            val = res.group(2).strip() if res is not None else des[i]
            if val.startswith("circuit") or val.startswith("superset"):
                i += 1
                continue

            val = self._clean_exercise(val)
            if len(val) > 3:
                self._exercises.add(val)

            i += 1

        return self._exercises

    @override
    def _enrich_tags(self, tags):
        tags = super()._enrich_tags(tags)
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
