import unittest
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import src.db.workout.models as models
from src.workout_sources.video_source import VideoSource
from src.utils import log
from src.utils.test_base import TestBase


class TestVideoSource(TestBase):
    def setUp(self):
        self.url = "www.test.com"
        self.db = MagicMock()
        self.vid = VideoSource(self.db, self.url, self.logger)

    def test_gen_tag_from_duration(self):
        with patch(
            __name__ + ".VideoSource.duration", new_callable=PropertyMock
        ) as mock_duration:
            mock_duration.return_value = timedelta(minutes=23)
            self.assertEqual(self.vid._gen_tag_from_duration(), "20-30min")
            mock_duration.return_value = timedelta(minutes=9)
            self.assertEqual(self.vid._gen_tag_from_duration(), "0-10min")
            mock_duration.return_value = timedelta(minutes=40)
            self.assertEqual(self.vid._gen_tag_from_duration(), "40-50min")

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
        self.vid._gen_tags = MagicMock()

        # removes/replaces ignored words/dupes only if the whole string matches
        self.vid._gen_tags.return_value = {
            "#stayhome",
            "some other tag",
            "#stayhome and other things",
            "apartment friendly",
            "apartment friendly qq",
        }
        self.assertEqual(
            self.vid.tags,
            {
                "some other tag",
                "#stayhome and other things",
                "no jumping",
                "apartment friendly qq",
            },
        )

        del self.vid.tags
        # progressively strips tags to prevent repeats
        self.vid._gen_tags.return_value = {
            "many words",
            "words",
            "a whole sentence of words",
            "sentence",
        }
        self.assertEqual(self.vid.tags, {"words", "sentence", "many", "a whole of"})

        del self.vid.tags
        # test progressive flow
        self.vid._gen_tags.return_value = {
            "apples",
            "apple and bananas",
            "bananas and apples, kiwi",
        }
        self.assertEqual(self.vid.tags, {"apples", "kiwi", "bananas"})

    def test_add_from_text(self):
        val = "workout with hiit and low impact"
        self.assertEqual(self.vid._add_from_text(val), {"hiit", "low impact"})

        val = "blah blah strengtharms blah"
        self.assertEqual(self.vid._add_from_text(val), set())

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

    def test_gen_tags(self):
        with (
            patch(
                __name__ + ".VideoSource.title",
                new_callable=PropertyMock,
                return_value="workout with hiit and low impact",
            ) as mock_title,
            patch(
                __name__ + ".VideoSource.duration",
                new_callable=PropertyMock,
                return_value=timedelta(minutes=23),
            ) as mock_duration,
        ):
            self.assertEqual(
                self.vid._gen_tags(),
                {
                    "hiit",
                    "low impact",
                    "20-30min",
                },
            )
