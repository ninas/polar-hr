import unittest
import json
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import src.db.workout.models as models
from src.utils import log
from src.utils.test_base import TestBase
from src.api.db_base import DBBase
import swagger_server.models as api_models


class TestDBBase(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Let's create our test DB
        cls.db = cls.create_test_db()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.teardown_test_db()

    def setUp(self):
        self.base = DBBase(self.db, self.logger, True)

    def test_by_id(self):
        vals = {
            models.SourcesMaterialized.id: [2, 5],
            models.SourcesMaterialized.url: ["https://youtube.com/source1"],
        }
        mod = self.base.by_id(models.SourcesMaterialized, vals)
        self.assertEqual(len(mod["data"]), 2)

        vals = {
            models.SourcesMaterialized.id: [1, 2, 5],
            models.SourcesMaterialized.url: ["https://youtube.com/source1"],
        }
        mod = self.base.by_id(models.SourcesMaterialized, vals)
        self.assertEqual(len(mod["data"]), 2)

        vals = {}
        mod = self.base.by_id(models.SourcesMaterialized, vals)
        self.assertEqual(len(mod["data"]), 3)

    def test_get_all(self):
        results = self.base.get_all(models.WorkoutsMaterialized)
        self.assertEqual(len(results["data"]), 4)
        # Ensure [None] gets converted to []
        self.assertEqual(results["data"][2]["equipment"], [])

        # We haven't defined a handler for this model
        results = self.base.get_all(models.Workouts.sources.get_through_model())
        self.assertEqual(results["data"], [])
