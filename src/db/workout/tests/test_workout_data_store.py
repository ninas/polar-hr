from collections import defaultdict
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch
import json
from datetime import datetime

from src.utils.test_base import TestBase
from src.db.workout.workout_data_store import WorkoutDataStore

import src.db.workout.models as models


class TestWorkoutDataStore(TestBase):
    def setUp(self):
        self.data = self.data()
        self.workout = WorkoutDataStore(self.data)

    def data(self):
        with open("src/db/workout/tests/sample_data.json") as f:
            return json.loads(f.read())

    def test_sport(self):
        # sample data starts with 'high-intensity interval training'
        self.assertEqual(self.workout.sport, "hiit")

        del self.workout.sport
        self.workout._i_data["sport"] = "CIRCUIT TRAINING"
        self.assertEqual(self.workout.sport, "circuit")

        del self.workout.sport
        self.workout._i_data["sport"] = "stretching"
        self.assertEqual(self.workout.sport, "stretching")

    def test_heart_rate_range(self):
        self.assertEqual(
            self.workout.heart_rate_range, {"avg": 130, "max": 171, "min": 66}
        )

        del self.workout.heart_rate_range
        del self.workout._i_data["heart_rate"]
        self.assertEqual(self.workout.heart_rate_range, {"min": 0, "max": 0, "avg": 0})

    def test_get_datetime(self):
        base = datetime.fromisoformat("2022-11-24T04:58:45.046000+00:00")
        # Default val includes timezone
        self.assertEqual(self.workout.get_datetime("end_time"), base)

        # No timezone, and no timezone info, will default to PDT
        self.workout._i_data["test_dt"] = "2022-11-23T21:58:45.046000"
        self.assertEqual(self.workout.get_datetime("test_dt"), base)

        self.workout._i_data["test_dt"] = "2022-11-23T22:58:45.046000"
        self.workout._i_data["start_time_utc_offset"] = -360
        self.assertEqual(self.workout.get_datetime("test_dt"), base)
