from google.cloud import secretmanager
import psycopg2
from collections import defaultdict
import os, json, datetime, re, copy, math, isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils import get_secret


class YTConsts:
    ignore_tags = {
        "thin legs workout",
        "activation",
        "high",
        "metabolism boosting",
        "tight hips",
        "inner and outer thigh slimming workout",
        "get toned",
        "fitness",
        "workouts for women",
        "workout at home",
        "workout from home",
        "home workout",
        "hitt",
        "home",
        "six pack workout",
        "full length workout",
        "quiet",
        "lower body  no weights",
        "no repeets",
        "no repeet",
        "fat burning",
        "no talking",
        "no talking workout",
        "heather robinson",
        "flat abs",
        "quick workout",
        "tiny waist round butt",
        "#withme",
        "thin arms",
        "slim arms",
        "arm slimming",
        "back fat workout",
        "2 week",
        "14 day",
        "hit",
        "fit",
        "arm toning without weights",
        "bat wings workout",
        "full length workout video",
        "from home",
        "for women",
        "slimming",
        "get abs",
        "weight loss workout",
        "day",
        "sholder",
        "#stayhome",
        "40min",
        "40 min",
        "30min",
        "30 min",
        "30 minute",
        "60 minute",
        "10 minute",
        "10min",
        "10 min",
        "20min",
        "20 min",
        "45 minute",
        "11 minute ab workout",
        "hr12week 2.0 day 8",
        "20",
        "2 week workout program",
        "60 minute workout with dumbbells",
        "be more flexible",
        "build a butt",
        "build lean muscle",
        "build muscle and burn fat",
        "build strength workout",
        "chizzled back",
        "chizzled chest",
        "condo workout",
        "corona workout",
        "intense workout",
        "intensity",
        "workout for legs",
        "tighten skin workout",
        "living room workout",
        "workout for 10 minutes a day",
        "workout for 10 minutes",
        "heatherrobertson fierce",
        "and",
        "women",
        "bootcamp workout",
        "how to glow up",
        "get toned arms",
        "lean and strong",
        "no gym workout",
        "get stronger",
        "with me",
        "free workouts",
        "workout for people who get bored",
        "get fit from home",
        "stay home workout",
        "workout for building strength",
        "round booty",
        "rounder butt",
        "bodyweight booty workout",
        "long lean body workout",
        "long and lean",
        "quick daily workout",
        "burn fat",
        "but",
        "dumbbell  for",
        "fat",
        "heather robertson fierce",
        "fitness challenge",
        "for",
        "workout for weight loss",
        "tabata for beginners",
        "for relaxation",
        "for sore muscles",
        "free workout program",
        "workout from anywhere",
        "full",
        "full length hiit workout",
        "get lean workout",
        "get shredded",
        "improve flexibility",
        "increase metabolism",
        "ing",
        "noise",
        "lose",
        "challenge",
        "conditioning",
        "body",
        "day 3",
        "30min hiit",
        "workouts for weight loss",
        "leg slimming workout",
        "thinner legs workout",
        "no gym workout at home",
        "quarantine workout",
        "real time workout",
        "relaxing",
        "routine",
        "series",
        "slim legs workout",
        "workout video",
        "wokrout",
    }

    strip_words = {
        "fat burning",
        " for strength",
        "sculpting",
        "home workout with",
        "workout challenge",
        "workout program",
        "workouts",
        "workout",
        "wrkout",
        "toning",
        "toned",
        "tight",
        "tighten",
        "exercises for",
        "exercises",
        "exercise",
        "sculpted",
        "for women",
        "only",
        "at home",
        "lean",
        "heather robinson",
        "hitt",
        "training",
        "circuit",
        "program",
        "from home",
        "shred",
        "quick",
        "11 line",
        "flat",
        "follow along",
        "strenth",
        "workout a day",
        "best",
        "brutal",
        "burn",
        "strong",
    }

    possible_tags = {
        "low impact",
        "hiit",
        "strength",
        "weights",
        "dumbbells",
        "cardio",
        "no jumping",
        "no equipment",
        "tabata",
        "core",
        "abs",
        "full body",
        "legs",
        "glutes",
        "booty",
        "arms",
        "chest",
        "shoulders",
        "triceps",
        "biceps",
        "delts",
        "upper body",
        "lower body",
        "total body",
        "mini-band",
    }

    expands = {
        "chest triceps and shoulder": {"chest", "triceps", "shoulder"},
        "abs and booty": {"abs", "butt"},
        "chest and back": {"chest", "back"},
        "legs and glutes": {"legs", "glutes"},
        "total body dumbbell": {"full body", "weights"},
        "upper body strength": {"upper body", "strength"},
        "arm and ab": {"arms", "abs"},
        "arms and abs": {"arms", "abs"},
        "full body hiit": {"full body", "hiit"},
        "low impact cardio": {"low impact", "cardio"},
        "full body stretch": {"full body", "stretching"},
        "no repeat   weights": {"no repeats", "weights"},
        "no repeat hiit": {"no repeats", "hiit"},
        "pilates hiit": {"pilates", "hiit"},
        "strength   dumbells": {"strength", "weights"},
        "strength and cardio": {"strength", "cardio"},
        "total body   dumbbells": {"full body", "weights"},
        "total body hiit": {"full body", "hiit"},
        "total body strength": {"full body", "strength"},
    }

    dedupes = {
        "10 minute total body workout": "full body",
        "metabolic": "metcon",
        "metabolic conditioning": "metcon",
        "metcan": "metcon",
        "dumbbells": "weights",
        "dumbells": "weights",
        "dumbell": "weights",
        "dumbbell": "weights",
        "booty": "butt",
        "flute": "butt",
        "glutes": "butt",
        "bum": "butt",
        "arm": "arms",
        "total body": "full body",
        "ab": "abs",
        "no repeat": "no repeats",
        "superset": "supersets",
        "strenth": "strength",
        "stregnth": "strength",
        "no weights": "no equipment",
        "strenght": "strength",
        "non repetitive": "no repeats",
        "apartment friendly": "no jumping",
        "no weight": "no equipment",
        "compound": "metcon",
        "body weight": "no equipment",
        "uper body": "upper body",
        "leg": "legs",
        "bodyweight": "no equipment",
        "super set": "supersets",
        "super sets": "supersets",
        "sholders": "shoulders",
        "40s work +20s rest": "40s work + 20s rest",
        "body-weight": "no equipment",
        "body-weighted": "no equipment",
        "no dumbbells": "no equipment",
        "no equiment": "no equipment",
        "booty  with band": "mini-band",
        "band": "mini-band",
        "non repetative": "no repeats",
        "bicep": "biceps",
        "bootie": "butt",
        "for entire body": "full body",
        "for people who get bored": "no repeats",
        "guided stretch": "stretching",
        "stretch": "stretching",
        "stretches": "stretching",
        "stretching routine": "stretching",
        "knee safe": "knee friendly",
        "leg day": "legs",
        "glow up challenge": "glow up",
        "glute": "glutes",
        "hips stretch": "hip stretch",
        "hip stretches": "hip stretch",
        "mini band": "mini-band",
        "no repetitive": "no repeats",
        "no squats no lunges": "knee friendly",
        "no weights glute": "no equipment",
        "out equipment": "no equipment",
        "out weights": "no equipment",
        "post  stretch": "stretching",
        "recovery stretch": "stretching",
        "shoulders": "shoulder",
        "stretch for hips": "hip stretch",
        "stretch for relaxation": "stretching",
        "stretch for sore muscles": "stretching",
        "stretches for hips": "hip stretch",
        "tricep": "triceps",
        "weight": "weights",
    }

    mappings = {
        "triceps": "arms",
        "biceps": "arms",
        "delts": "arms",
        "abs": "core",
        "arms": "upper body",
    }

    id_regex = re.compile("^.*(?:(?:youtu\.be\/|v\/|vi\/|u\/\w\/|embed\/|shorts\/)|(?:(?:watch)?\?v(?:i)?=|\&v(?:i)?=))([^#\&\?]*).*")

    chapters_regex = re.compile("(\d{0,2}:?\d{1,2}:\d{2})?(.+)")


class YoutubeVid:
    def __init__(self, url):
        self.url = url
        self._tags = None
        self._data = None
        self._vid_id = None
        self._exercises = None
        self.source_tags = defaultdict(set)


    @staticmethod
    def is_youtube_vid(url):
        return "youtu" in url

    @property
    def vid_id(self):
        if self._vid_id is not None:
            return self._vid_id
        m = YTConsts.id_regex.match(self.url)
        if m is None:
            raise Exception(f"Unable to find id in url: {url}")
        self._vid_id = m.group(1)
        return self._vid_id

    @property
    def api_key(self):
        return get_secret("youtube_api_key")

    @property
    def data(self):
        if self._data is not None:
            return self._data
        # https://www.googleapis.com/youtube/v3/videos?id=Mvo2snJGhtM&key=AIzaSyAfI65NHBKi10chwT4i3BPb8GcQvg4kM3o&part=snippet,contentDetails
        youtube_client = build(
            "youtube", "v3", developerKey=self.api_key)

        try:
            results = youtube_client.videos().list(
                part='snippet,contentDetails',
                id=self.vid_id
            ).execute()
        except HttpError as e:
            print(f"A HTTP error {e.resp.status} occurred:\n{e.content}")
            self._data = None
            return

        if len(results["items"]) != 1:
            raise Exception(f"Unexpectedly shaped youtube data object: {self.url} : {self.vid_id} \n {results}")
        self._data = results["items"][0]
        return self._data

    @property
    def tags(self):
        if self._tags is not None:
            return self._tags

        tags = set()
        strip_words = sorted(list(copy.deepcopy(YTConsts.strip_words)),
                             key=len, reverse=True)

        for i in sorted(self.data["snippet"]["tags"], key=len):
            i = i.lower()
            starter = i
            print("\t",i)
            if i in YTConsts.ignore_tags:
                continue

            if i in YTConsts.dedupes:
                i = YTConsts.dedupes[i]
            for j in strip_words:
                i = re.sub(j + r"\b", "", i)
                i = re.sub(r"\s+", " ", i)

            for t in ["s", "and", "with"]:
                if i.startswith(f"{t} "):
                    i = i[len(t):]
                if i.endswith(f" {t}"):
                    i = i[:-len(t)]

            i = i.strip()

            if i in YTConsts.ignore_tags:
                continue

            if len(i) >= 3:
                print(i)
                tags.add(i)
                self.source_tags[i].add(starter)
                strip_words.append(i)
                if len(i.split(" ")) == 1 and i[-1] == "s":
                    strip_words.append(i[:-1])
                strip_words = sorted(strip_words, key=len, reverse=True)



        self._tags = self.enrich_tags(tags)

        return self._tags

    def enrich_tags(self, tags):
        for i in YTConsts.possible_tags:
            if i in tags:
                continue
            elif (i in self.data["snippet"]["title"] or
                  i in self.data["snippet"]["description"]):
                tags.add(i)

        for r in range(2):
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

            tags.update(to_add)
            tags = tags - to_remove


        for k, v in YTConsts.mappings.items():
            if k in tags and v not in tags:
                tags.add(v)

        on_off = re.compile("(\d{2}s.+\d{2}s rest)")
        res = on_off.search(self.data["snippet"]["description"])
        if res is not None:
            result = res.group(1)
            result = result.replace(" of", "")
            result = result.replace("workout", "work")
            if len(res.group(1)) > 20:
                result = result[:20]
            tags.add(result.strip())

        tags.add(self.data["snippet"]["channelTitle"].lower())

        in_mins = self.duration.total_seconds() / 60
        tags.add(
            f"{int(in_mins/10)*10}-{math.ceil(in_mins/10)*10}min")


        return tags

    @property
    def title(self):
        return self.data["snippet"]["title"]

    @property
    def duration(self):
        return isodate.parse_duration(self.data["contentDetails"]["duration"])

    @property
    def exercises(self):
        if self._exercises is not None:
            return self._exercises

        description = self.data["snippet"]["description"].lower()

        self._exercises = set()

        wu = "workout breakdown"
        loc = description.find(wu)
        if loc < 0:
            return self._exercises
        start = description.find("\n", loc)

        des = description[start:].split("\n")

        i = 0

        while i < len(des):
            if len(des[i]) == 0 or "circuit" in des[i] or "rest" in des[i] or "intro" in des[i] or "warm up" in des[i]:
                i += 1
                continue
            elif "cool down" in des[i] or len(des[i]) > 150 or "equipment needed" in des[i]:
                break

            val = YTConsts.chapters_regex.match(des[i])
            if val is None:
                i += 1
                continue
            val = val.group(2)
            if val.endswith("(l)") or val.endswith("(r)"):
                val = val[0:-4]
            if len(val) > 3:
                self._exercises.add(val.strip())

            i += 1

        return self._exercises


if __name__ == "__main__":
    a = YoutubeVid("https://www.youtube.com/watch?v=g-i3S1fnQbQ")
    print(a.tags)
    print(a.exercises)
