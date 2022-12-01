import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock
from datetime import timedelta

from source import Source, ExistingSource, UnknownSource
import db.models as models


class TestSource(unittest.TestCase):
    YOUTUBE_URL = "https://www.youtube.com/watch?v=something"

    def setUp(self):
        self.url = "www.test.com"
        self.data_return = {"snippet": {}}
        self.db = MagicMock()
        self.source = Source(self.db, self.url, self.data_return)

    def test_normalise(self):
        self.assertEqual(
            Source.normalise_url(self.YOUTUBE_URL), "https://www.youtu.be/something"
        )
        self.assertEqual(Source.normalise_url("unknown"), "unknown")

    def test_load_source(self):
        Source._find = MagicMock(return_value="something")
        self.assertTrue(
            isinstance(Source.load_source(MagicMock(), self.url), ExistingSource)
        )

        Source._find = MagicMock(return_value=None)
        self.assertTrue(
            isinstance(Source.load_source(MagicMock(), self.url), UnknownSource)
        )

    @patch("source.models.Sources")
    def test_insert_row(self, mock_src_model):
        self.source.model = MagicMock(tags=MagicMock())
        self.source.insert_row()
        self.source.model.tags.assert_not_called()

        with patch(__name__ + ".Source.tags", new_callable=PropertyMock) as tags_mock:
            tags_mock.return_value = ["one", "two"]
            self.source._insert_basic_model_data = MagicMock()

            self.source.insert_row()
            self.source._insert_basic_model_data.assert_called_with(
                tags_mock.return_value, models.Tags
            )
