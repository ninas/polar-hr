import unittest
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from src.db.workout.youtube import HeatherRobertsonYoutube, Youtube
from src.db.workout.youtube_consts import YTConsts
from src.utils.test_base import TestBase


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

    def test_strip_words(self):
        # only removes if not in the middle of a word
        words = ["test", "2", "ing"]
        self.assertEqual(self.vid._strip_words(words, "testing"), "testing")
        self.assertEqual(self.vid._strip_words(words, "test"), "")
        self.assertEqual(self.vid._strip_words(words, "live2poop"), "live2poop")
        self.assertEqual(
            self.vid._strip_words(words, "testing  things"), "testing things"
        )

    def test_remove_helper_words(self):
        self.assertEqual(self.vid._remove_helper_words("testing s"), "testing")
        self.assertEqual(
            self.vid._remove_helper_words("in and middle"), "in and middle"
        )
        self.assertEqual(self.vid._remove_helper_words("with friends"), "friends")

    def test_tags_basic(self):
        func1 = lambda x: x
        mock1 = Mock(side_effect=func1)
        self.vid._enrich_tags = mock1

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
                # this gets automatically added by Source
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

    def test_add_from_description(self):
        self.data_return["snippet"]["title"] = "workout with hiit and low impact"
        self.data_return["snippet"]["description"] = "blah blah strength blah"

        self.assertEqual(
            self.vid._add_from_description(), {"hiit", "low impact", "strength"}
        )

    def test_semantically_update(self):

        self.assertEqual(
            self.vid._semantically_update({"total body hiit"}), {"full body", "hiit"}
        )

        self.assertEqual(
            self.vid._semantically_update(
                {
                    "total body hiit",
                    "total body",
                    "no equipment",
                    "weights",
                    "no jumping",
                    "jumping",
                    "legs",
                    "leg",
                }
            ),
            {"full body", "hiit", "no equipment", "no jumping", "legs", "lower body",},
        )

    def test_enrich_tags(self):

        self.data_return["snippet"]["title"] = "workout with hiit and low impact"
        self.data_return["snippet"]["description"] = "blah blah strength blah"

        tags = {
            "upper body superset",
            "no equipment",
            "dumbbells",
            "jumping",
        }

        self.assertEqual(
            self.vid._enrich_tags(tags),
            {
                "hiit",
                "upper body",
                "supersets",
                "no equipment",
                "jumping",
                "strength",
                "low impact",
            },
        )

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
        test_vid_id = "dQw4w9WgXcQ"
        test_urls = [
            f"https://youtube.com/shorts/{test_vid_id}?feature=share",
            f"//www.youtube-nocookie.com/embed/{test_vid_id}?rel=0",
            f"http://www.youtube.com/user/Scobleizer#p/u/1/{test_vid_id}",
            f"https://www.youtube.com/watch?v={test_vid_id}&feature=channel",
            f"http://www.youtube.com/watch?v={test_vid_id}&playnext_from=TL&videos=osPknwzXEas&feature=sub",
            f"http://www.youtube.com/ytscreeningroom?v={test_vid_id}",
            f"http://www.youtube.com/user/SilkRoadTheatre#p/a/u/2/{test_vid_id}",
            f"http://youtu.be/{test_vid_id}",
            f"http://www.youtube.com/watch?v={test_vid_id}&feature=youtu.be",
            f"http://youtu.be/{test_vid_id}",
            f"https://www.youtube.com/user/Scobleizer#p/u/1/{test_vid_id}?rel=0",
            f"http://www.youtube.com/watch?v={test_vid_id}&feature=channel",
            f"http://www.youtube.com/watch?v={test_vid_id}&playnext_from=TL&videos=osPknwzXEas&feature=sub",
            f"http://www.youtube.com/ytscreeningroom?v={test_vid_id}",
            f"http://www.youtube.com/embed/{test_vid_id}?rel=0",
            f"http://www.youtube.com/watch?v={test_vid_id}",
            f"http://youtube.com/v/{test_vid_id}?feature=youtube_gdata_player",
            f"http://youtube.com/vi/{test_vid_id}?feature=youtube_gdata_player",
            f"http://youtube.com/?v={test_vid_id}&feature=youtube_gdata_player",
            f"http://www.youtube.com/watch?v={test_vid_id}&feature=youtube_gdata_player",
            f"http://youtube.com/?vi={test_vid_id}&feature=youtube_gdata_player",
            f"http://youtube.com/watch?v={test_vid_id}&feature=youtube_gdata_player",
            f"http://youtube.com/watch?vi={test_vid_id}&feature=youtube_gdata_player",
            f"http://youtu.be/{test_vid_id}?feature=youtube_gdata_player",
            f"www.youtu.be/{test_vid_id}",
        ]

        for u in test_urls:
            self.assertEqual(Youtube.youtube_vid_id(u), test_vid_id)


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
