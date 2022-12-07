import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock
from datetime import timedelta

from youtube import Youtube, HeatherRobertsonYoutube
from youtube_consts import YTConsts


class TestYoutube(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.url = "www.youtu.be/test"
        self.data_return = {"snippet": {"channelTitle": "Heather Robertson"}}

        self.vid = Youtube(self.db, self.url, self.data_return)
        Youtube.get_data = MagicMock(return_value=self.data_return)

    def test_load_source(self):
        self.assertTrue(
            isinstance(Youtube.load_source(self.db, self.url), HeatherRobertsonYoutube)
        )

        self.data_return["snippet"]["channelTitle"] = "something"
        self.assertTrue(isinstance(Youtube.load_source(self.db, self.url), Youtube))

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
            },
        )

        self.vid._tags = None
        # progressively strips tags to prevent repeats
        self.data_return["snippet"]["tags"] = [
            "many words",
            "words",
            "a whole sentence of words",
            "sentence",
        ]
        self.assertEqual(self.vid.tags, {"words", "sentence", "many", "a whole of"})

        self.vid._tags = None
        # test progressive flow
        self.data_return["snippet"]["tags"] = [
            "apples",
            "apple and bananas",
            "bananas and apples, kiwi",
        ]
        self.assertEqual(self.vid.tags, {"apples", "kiwi", "bananas"})

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
            {
                "full body",
                "hiit",
                "no equipment",
                "no jumping",
                "legs",
                "lower body",
            },
        )

    def test_gen_from_duration(self):
        with patch(
            __name__ + ".Youtube.duration", new_callable=PropertyMock
        ) as mock_duration:
            mock_duration.return_value = timedelta(minutes=42)
            self.assertEqual(self.vid._gen_tag_from_duration(), "40-50min")

            mock_duration.return_value = timedelta(minutes=40)
            self.assertEqual(self.vid._gen_tag_from_duration(), "40-50min")

            mock_duration.return_value = timedelta(minutes=7)
            self.assertEqual(self.vid._gen_tag_from_duration(), "0-10min")

    def test_enrich_tags(self):

        self.data_return["snippet"]["title"] = "workout with hiit and low impact"
        self.data_return["snippet"]["description"] = "blah blah strength blah"

        tags = {
            "upper body superset",
            "no equipment",
            "dumbbells",
            "jumping",
        }

        with patch(
            __name__ + ".Youtube.creator", new_callable=PropertyMock
        ) as mock_channel:
            mock_channel.return_value = "channel title"
            self.vid._gen_tag_from_duration = MagicMock(return_value="10-20min")
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
                    "channel title",
                    "10-20min",
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


class TestHeatherRobertsonYoutube(TestYoutube):
    def setUp(self):
        super().setUp()
        self.vid = HeatherRobertsonYoutube(self.db, self.url, self.data_return)

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
        self.vid._exercises = None

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
        self.vid._exercises = None

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
        self.vid._exercises = None

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
        self.vid._exercises = None

        self.assertEqual(
            self.vid.exercises, {"exercise 1", "exercise 2", "exercise 3", "exercise 4"}
        )