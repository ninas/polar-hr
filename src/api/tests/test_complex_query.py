import unittest
import json
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch
import testing.postgresql

from src.utils import log
from src.utils.test_base import TestBase
from src.api.complex_query import ComplexQuery
from swagger_server.models import *
from src.db.workout import models
from src.api.db_base import DBBase


class TestComplexQuery(TestBase):
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
        self.base = DBBase(self.db, self.logger, False)

    def _gen_query(self, source_params={}, workout_params={}):
        source = SourceQueryParams(**source_params)
        workout = WorkoutQueryParams(**workout_params)
        return Query(source, workout)

    def test_query_sources_tags(self):
        # tags should be ANDed not ORed
        cq = self._gen_query({"tags": ["tag1", "tag2"]}, {},)
        quer = self.base.query(models.SourcesMaterialized, cq)
        self.assertEqual(len(quer["data"]), 1)

        cq = self._gen_query({"tags": ["tag2"]}, {},)
        quer = self.base.query(models.SourcesMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)

    def test_query_sources_basic(self):
        cq = self._gen_query(
            {"tags": ["tag2"], "length_min": 20 * 60}, {"sport": ["sport1"]},
        )
        quer = self.base.query(models.SourcesMaterialized, cq)
        self.assertEqual(len(quer["data"]), 2)

        # query params are ANDed
        cq = self._gen_query(
            {"tags": ["tag2"], "length_min": 20 * 60, "exercises": ["exercise5"]}, {}
        )
        quer = self.base.query(models.SourcesMaterialized, cq)
        self.assertEqual(len(quer["data"]), 1)

        cq = self._gen_query(
            {"tags": ["tag2"], "length_min": 20 * 60, "exercises": ["exercise5"]},
            {"sport": ["sport1"]},
        )
        quer = self.base.query(models.SourcesMaterialized, cq)
        self.assertEqual(len(quer["data"]), 0)

    def test_query_sources_on_workout(self):
        cq = self._gen_query({}, {"sport": ["sport1"]},)
        quer = self.base.query(models.SourcesMaterialized, cq)
        self.assertEqual(len(quer["data"]), 2)

        cq = self._gen_query({}, {"hr_range": HRRange(101, 180)})
        quer = self.base.query(models.SourcesMaterialized, cq)
        self.assertEqual(len(quer["data"]), 1)

    def test_query_workouts_filter_on_sources(self):
        cq = self._gen_query({"tags": ["tag2"]}, {"sport": ["sport1"]},)
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)

    def test_query_workouts_samples(self):
        cq = self._gen_query({}, {"sport": ["sport1"], "samples": True})
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        for i in quer["data"]:
            self.assertTrue("samples" in i)

        cq = self._gen_query({}, {"sport": ["sport1"], "samples": False})
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        for i in quer["data"]:
            self.assertTrue("samples" not in i)

    def test_query_workouts_in_hr_zones(self):
        cq = self._gen_query(
            {},
            {
                "in_hr_zone": [
                    HRZoneRange(zone_type="70_80", min_time="PT5M", max_time="PT12M")
                ]
            },
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 2)

        # If the same field is provided more than once, the max/min should be used
        cq = self._gen_query(
            {},
            {
                "in_hr_zone": [
                    HRZoneRange(zone_type="70_80", min_time="PT8M", max_time="PT12M"),
                    HRZoneRange(zone_type="70_80", min_time="PT5M", max_time="PT10M"),
                    HRZoneRange(zone_type="70_80", min_time="PT6M", max_time="PT11M"),
                ]
            },
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 2)

        # Queries should be ANDed - a workout must have HRZones that match all the ones specified
        cq = self._gen_query(
            {},
            {
                "in_hr_zone": [
                    HRZoneRange(zone_type="50_60", max_time="PT1M"),
                    HRZoneRange(zone_type="70_80", min_time="PT5M", max_time="PT10M"),
                ]
            },
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 1)

    def test_query_workouts_above_hr_zones(self):
        cq = self._gen_query(
            {}, {"above_hr_zone": [HRZoneAbove(zone_type="70_80", min_time="PT11M",)]},
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 1)

        # if percentage is provided, the time fields should be ignored
        cq = self._gen_query(
            {},
            {
                "above_hr_zone": [
                    HRZoneAbove(
                        zone_type="70_80", min_time="PT11M", percent_spent_above=25.0,
                    )
                ]
            },
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)

        # If the same field is provided more than once, the max/min should be used
        # If percent is provided once, then that should be used instead of any min times
        cq = self._gen_query(
            {},
            {
                "above_hr_zone": [
                    HRZoneAbove(zone_type="70_80", min_time="PT0M"),
                    HRZoneAbove(zone_type="70_80", percent_spent_above=25.0),
                    HRZoneAbove(zone_type="70_80", min_time="PT1M"),
                ]
            },
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)

        # Queries should be ANDed - a workout must have HRZones that match all the ones specified
        cq = self._gen_query(
            {},
            {
                "above_hr_zone": [
                    HRZoneAbove(zone_type="90_100", min_time="PT4M"),
                    HRZoneAbove(zone_type="70_80", percent_spent_above=10.0),
                ]
            },
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 2)

    def test_query_workouts_equipment(self):
        # If only equipment type is specified, fetch all that use any magnitude of that type
        cq = self._gen_query({}, {"equipment": [Equipment(equipment_type="weights")]})
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)

        # If no equipment params specified, fetch all
        cq = self._gen_query({}, {"sport": ["sport1"]})
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)
        cq = self._gen_query({}, {"sport": ["sport1"], "equipment": []})
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)
        cq = self._gen_query({}, {"sport": ["sport1"], "equipment": [Equipment()]})
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)

        # Which is different to when "No equipment" is specifically searched for
        cq = self._gen_query({}, {"equipment": [Equipment(equipment_type="none")]})
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 1)

        # Different searches are ORed
        cq = self._gen_query(
            {},
            {
                "equipment": [
                    Equipment(equipment_type="bands", magnitude="medium"),
                    Equipment(equipment_type="none"),
                ]
            },
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 2)

        cq = self._gen_query(
            {},
            {
                "equipment": [
                    Equipment(equipment_type="bands", magnitude="medium"),
                    Equipment(equipment_type="weights", magnitude="8"),
                ]
            },
        )
        quer = self.base.query(models.WorkoutsMaterialized, cq)
        self.assertEqual(len(quer["data"]), 3)
