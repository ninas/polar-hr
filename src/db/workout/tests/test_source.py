import unittest
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import src.db.workout.models as models
from src.db.workout.source import ExistingSource, Source, UnknownSource
from src.utils import log
from src.utils.test_base import TestBase


class TestSource(TestBase):
    YOUTUBE_URL = "https://www.youtube.com/watch?v=something"

    def setUp(self):
        self.url = "www.test.com"
        self.data_return = {"snippet": {}}
        self.db = MagicMock()
        self.source = Source(self.db, self.url, self.data_return, self.logger)

        self.source._insert_tags = MagicMock(side_effect=lambda a,b: a)

    def test_normalise(self):
        self.assertEqual(
            Source.normalise_url(self.YOUTUBE_URL), "https://www.youtu.be/something"
        )
        self.assertEqual(Source.normalise_url("unknown"), "unknown")

    def test_load_source(self):
        Source._find = MagicMock(return_value="something")
        self.assertTrue(
            isinstance(
                Source.load_source(MagicMock(), self.url, self.logger), ExistingSource
            )
        )

        Source._find = MagicMock(return_value=None)
        self.assertTrue(
            isinstance(
                Source.load_source(MagicMock(), self.url, self.logger), UnknownSource
            )
        )

    def test_gen_tag_from_duration(self):
        with patch(
            __name__ + ".Source.duration", new_callable=PropertyMock
        ) as mock_duration:
            mock_duration.return_value = timedelta(minutes=23)
            self.assertEqual(self.source._gen_tag_from_duration(), "20-30min")
            mock_duration.return_value = timedelta(minutes=9)
            self.assertEqual(self.source._gen_tag_from_duration(), "0-10min")
            mock_duration.return_value = timedelta(minutes=40)
            self.assertEqual(self.source._gen_tag_from_duration(), "40-50min")

    def test_all_tags_added(self):

        with (patch(
            __name__ + ".Source.creator",
            new_callable=PropertyMock,
            return_value="creator",
        ) as mock_creator,
        patch(
            __name__ + ".Source.exercises",
            new_callable=PropertyMock,
            return_value=["ex1", "ex2"],
        ) as mock_exercises,
        patch(
            __name__ + ".Source.duration",
            new_callable=PropertyMock,
            return_value=timedelta(minutes=23),
        ) as mock_duration,
        patch(__name__ + ".models.Sources.create") as mock_model):
            mm = MagicMock()
            mock_model.return_value = MagicMock(tags=MagicMock(add=mm))
            self.source.insert_row()
            self.assertEqual(set(*(mm.call_args.args)), {
                "creator",
                "ex1",
                "ex2",
                "20-30min"
            })
