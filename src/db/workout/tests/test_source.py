import unittest
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import src.db.workout.models as models
from src.db.workout.source import ExistingSource, Source, UnknownSource
from src.utils import log
from src.utils.test_base import TestBase, TestConsts


class TestSource(TestBase):
    def setUp(self):
        self.url = "www.test.com"
        self.db = MagicMock()
        self.source = Source(self.db, self.url, self.logger)

        self.source._insert_tags = MagicMock(side_effect=lambda a, b: a)

    def test_normalise(self):
        self.assertEqual(
            Source.normalise_url("https://www.youtube.com/watch?v=something"),
            "https://www.youtu.be/something",
        )
        self.assertEqual(Source.normalise_url("unknown"), "unknown")

    def test_get_source_type(self):
        for i in TestConsts.YOUTUBE_URLS:
            self.assertEqual(Source.get_source_type(i).source_type, models.SourceType.YOUTUBE)

        for i in [
            "fiton:5567",
            "https://app.fitonapp.com/browse/workout/5567",
            "https://share.fitonapp.com/html/invite-message/5600d08ac57544ab829c680df6a87f04",
        ]:
            self.assertEqual(Source.get_source_type(i).source_type, models.SourceType.FITON)

        self.assertEqual(
                Source.get_source_type("www,youtube.com/fiton/something").source_type, models.SourceType.YOUTUBE
            )

        self.assertEqual(Source.get_source_type("test").source_type, models.SourceType.UNKNOWN)

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

    def test_all_tags_added(self):

        with (
            patch(
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
                __name__ + ".Source.tags",
                new_callable=PropertyMock,
                return_value=["tag1", "tag2"],
            ) as mock_duration,
            patch(__name__ + ".models.Sources.create") as mock_model,
        ):
            mm = MagicMock()
            mock_model.return_value = MagicMock(tags=MagicMock(add=mm))
            self.source.insert_row()
            self.assertEqual(
                set(*(mm.call_args.args)),
                {
                    "creator",
                    "ex1",
                    "ex2",
                    "tag1",
                    "tag2",
                },
            )
