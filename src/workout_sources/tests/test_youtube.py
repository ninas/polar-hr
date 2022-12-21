import unittest
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from src.workout_sources.youtube import HeatherRobertsonYoutube, Youtube
from src.utils.test_base import TestBase, TestConsts


class TestYoutube(TestBase):
    def setUp(self):
        self.db = MagicMock()
        self.url = "www.youtu.be/test"
        self.data_return = {
            "snippet": {
                "channelTitle": "Heather Robertson",
                "title": "My workout title",
                "description": "My workout description",
            },
            "contentDetails": {"duration": "PT21M34S"},
        }
        self.vid = self._create_vid()
        Youtube.get_data = MagicMock(return_value=self.data_return)

    def _create_vid(self):
        return Youtube(self.db, self.url, self.data_return, self.logger)

    def test_load_source(self):
        self.assertTrue(
            isinstance(
                Youtube.load_source(self.db, self.url, self.logger),
                HeatherRobertsonYoutube,
            )
        )

        self.data_return["snippet"]["channelTitle"] = "something"
        self.assertTrue(
            isinstance(Youtube.load_source(self.db, self.url, self.logger), Youtube)
        )

    def test_normalise(self):
        self.assertEqual(
            Youtube.normalise_url("https://www.youtube.com/watch?v=something"),
            "https://www.youtu.be/something",
        )

    def test_tags_basic(self):

        # removes/replaces ignored words/dupes only if the whole string matches
        self.data_return["snippet"]["tags"] = [
            "#stayhome",
            "some other tag",
            "#stayhome and other things",
            "apartment friendly",
            "apartment friendly qq",
        ]
        self.assertEqual(
            self.vid.tags,
            {
                "some other tag",
                "#stayhome and other things",
                "no jumping",
                "apartment friendly qq",
                # this gets automatically added by VideoSource
                "20-30min",
            },
        )

        del self.vid.tags
        # progressively strips tags to prevent repeats
        self.data_return["snippet"]["tags"] = [
            "many words",
            "words",
            "a whole sentence of words",
            "sentence",
        ]
        self.assertEqual(
            self.vid.tags, {"words", "sentence", "many", "a whole of", "20-30min"}
        )

        del self.vid.tags
        # test progressive flow
        self.data_return["snippet"]["tags"] = [
            "apples",
            "apple and bananas",
            "bananas and apples, kiwi",
        ]
        self.assertEqual(self.vid.tags, {"apples", "kiwi", "bananas", "20-30min"})

    def test_exercises(self):
        self.data_return["snippet"]["description"] = (
            " something something\n"
            "more things\n"
            "0:00 Warmup\n"
            "0:10 Exercise 1\n"
            "some random string\n"
            "0:20 Exercise 2\n"
            "1:00:10 Exercise 3\n"
            "10: Testing\n"
            "More random stuff\n"
        )

        self.assertEqual(
            self.vid.exercises, {"warmup", "exercise 1", "exercise 2", "exercise 3"}
        )

    def test_clean_exercises(self):
        self.assertEqual(self.vid._clean_exercise("something (R)"), "something")
        self.assertEqual(
            self.vid._clean_exercise("something burn out"), "something burnout"
        )
        self.assertEqual(
            self.vid._clean_exercise("with a wordburnout"), "with a wordburnout"
        )

        self.assertEqual(self.vid._clean_exercise("- my workout"), "my workout")

    def test_vid_id(self):
        for u in TestConsts.YOUTUBE_URLS:
            self.assertEqual(Youtube.youtube_vid_id(u), TestConsts.YOUTUBE_ID)


class TestHeatherRobertsonYoutube(TestYoutube):
    def _create_vid(self):
        return HeatherRobertsonYoutube(self.db, self.url, self.data_return, self.logger)

    def test_hiit_intervals(self):
        self.data_return["snippet"]["description"] = (
            "something something\n"
            "workout breakdown\n"
            "some sentence 30s work + 30s rest\n"
            "something else\n"
        )

        self.assertEqual(self.vid._hiit_intervals(), {"30s work + 30s rest"})

    def test_exercises(self):
        self.data_return["snippet"]["description"] = (
            " something something\n"
            "more things\n"
            "equipment needed something\n"
            "workout breakdown something\n"
            "Intro\n"
            "0:00 Warm up\n"
            "0:05 Circuit 1\n"
            "0:10 Exercise 1\n"
            "Exercise 2\n"
            "0:20 Exercise 3\n"
            "1:00:10 Exercise 4\n"
            "Cool Down\n"
            "10: Testing\n"
            "More random stuff\n"
        )

        self.assertEqual(
            self.vid.exercises, {"exercise 1", "exercise 2", "exercise 3", "exercise 4"}
        )

        self.data_return["snippet"]["description"] = (
            " something something\n"
            "more things\n"
            "equipment needed something\n"
            "0:00 Warm up\n"
            "0:05 Circuit 1\n"
            "0:10 Exercise 1\n"
            "Exercise 2\n"
            "0:20 Exercise 3\n"
            "1:00:10 Exercise 4\n"
            "Cool Down\n"
            "10: Testing\n"
            "More random stuff\n"
        )
        del self.vid.exercises

        self.assertEqual(
            self.vid.exercises, {"exercise 1", "exercise 2", "exercise 3", "exercise 4"}
        )

        self.data_return["snippet"]["description"] = (
            " something something\n"
            "more things\n"
            "equipment needed something\n"
            "0:05 Circuit 1\n"
            "0:10 Exercise 1\n"
            "Exercise 2\n"
            "0:20 Exercise 3\n"
            "1:00:10 Exercise 4\n"
            "Cool Down\n"
            "10: Testing\n"
            "More random stuff\n"
        )
        del self.vid.exercises

        self.assertEqual(self.vid.exercises, set())

        self.data_return["snippet"]["description"] = (
            " something something\n"
            "more things\n"
            "equipment needed something\n"
            "0:00 Warm up\n"
            "0:05 Circuit 1\n"
            "0:10 Exercise 1\n"
            "Exercise 2\n"
            "0:20 Exercise 3\n"
            "1:00:10 Exercise 4\n"
            "equipment needed\n"
            "10: Testing\n"
            "More random stuff\n"
        )
        del self.vid.exercises

        self.assertEqual(
            self.vid.exercises, {"exercise 1", "exercise 2", "exercise 3", "exercise 4"}
        )

        self.data_return["snippet"]["description"] = (
            " something something\n"
            "more things\n"
            "equipment needed something\n"
            "0:00 Warm up\n"
            "0:05 Circuit 1\n"
            "0:10 Exercise 1\n"
            "Exercise 2\n"
            "0:20 Exercise 3\n"
            "1:00:10 Exercise 4\n"
            "10: Testing in a really really long string with lots of things in it\n"
            "More random stuff\n"
        )
        del self.vid.exercises

        self.assertEqual(
            self.vid.exercises, {"exercise 1", "exercise 2", "exercise 3", "exercise 4"}
        )
