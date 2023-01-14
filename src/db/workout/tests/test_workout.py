import json
import isodate
import unittest
from collections import defaultdict
from copy import deepcopy
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch
from peewee import fn

import src.db.workout.models as models
from src.db.workout.workout import Workout
from src.db.workout.workout_data_store import WorkoutDataStore
from src.utils.test_base import TestBase


class TestWorkout(TestBase):
    def setUp(self):
        self.raw_data = self.data()
        self.data = WorkoutDataStore(self.raw_data)

    def mock_through_workout(self):
        self.db = MagicMock()
        self.workout = Workout(self.db, self.data, self.logger)
        self.workout.equipment = self._mock_equipment()
        self.workout._insert_tags = MagicMock(side_effect=lambda a, b: a)
        self.workout.find = MagicMock(return_value=None)

    def data(self):
        with open("src/db/workout/tests/sample_data.json") as f:
            return json.loads(f.read())

    def test_insert_row(self):
        self.db = self.create_test_db()
        self.data._i_data["sources"] = ["www.test.com"]
        self.workout = Workout(self.db, self.data, self.logger)
        self.workout.insert_row()

        workouts = models.Workouts.select()
        self.assertEqual(len(workouts), 1)
        wrk = workouts[0]
        self.assertEqual(wrk.samples, self.data.samples)
        self.assertEqual(wrk.zone_below_50_upper, 103)
        self.assertEqual(wrk.zone_below_50_percentspentabove, 100)
        self.assertEqual(wrk.zone_60_70_duration, isodate.parse_duration("PT5M"))
        self.assertEqual(wrk.zone_90_100_percentspentabove, 11.493916)
        self.assertEqual(wrk.sport, "hiit")
        workout_tags = (
            models.Tags.select(models.Tags.name)
            .join(models.Workouts.tags.get_through_model())
            .where(fn.EXISTS(workouts))
        )
        self.assertEqual(len(workout_tags), 4)
        self.assertEqual(
            {"hiit", "5lbs", "8lbs", "weights"}, {i.name for i in workout_tags}
        )

        self.assertEqual(len(models.Sources.select()), 1)

        # Add duplicate
        self.workout = Workout(self.db, self.data, self.logger)
        self.workout.insert_row()
        self.assertEqual(len(workouts), 1)
        self.assertEqual(len(models.Sources.select()), 1)

        self.teardown_test_db()

    @patch("src.db.workout.workout.DBInterface.find", return_value=None)
    def test_exit_early(self, find):
        self.mock_through_workout()
        pop = MagicMock()

        def _create(dd):
            wd = WorkoutDataStore(dd)
            wrk = Workout(self.db, wd, self.logger)
            # Let's mock this so we can see if it's reached
            wrk._populate_model = pop
            return wrk

        d = deepcopy(self.raw_data)
        del d["start_time"]
        w = _create(d)
        self.assertEqual(w.insert_row(), None)
        pop.assert_not_called()

        d = deepcopy(self.raw_data)
        del d["samples"]
        w = _create(d)
        self.assertEqual(w.insert_row(), None)
        pop.assert_not_called()

        d = deepcopy(self.raw_data)
        w = _create(d)
        find.return_value = "something"

        self.assertEqual(w.insert_row(), "something")
        pop.assert_not_called()

    def _mock_equipment(self):
        equipment_mocks = []
        for i in self.data.equipment["weights"]:
            equipment_mocks.append(
                MagicMock(
                    equipmenttype=models.EquipmentType.WEIGHTS,
                    magnitude=i["magnitude"],
                    quantity=i["quantity"],
                )
            )
        return equipment_mocks

    def test_equipment_to_tags(self):
        self.mock_through_workout()
        self.assertEqual(
            self.workout._equipment_to_tags(), {"5lbs", "8lbs", "weights",},
        )

        equip = self._mock_equipment()
        equip.append(
            MagicMock(
                equipmenttype=models.EquipmentType.BANDS, magnitude="heavy", quantity=1,
            )
        )
        self.workout = Workout(self.db, self.data, self.logger)
        self.workout.equipment = equip
        self.assertEqual(
            self.workout._equipment_to_tags(),
            {"5lbs", "8lbs", "weights", "heavy band", "mini-band"},
        )

        self.workout = Workout(self.db, self.data, self.logger)
        self.workout.equipment = []
        self.assertEqual(self.workout._equipment_to_tags(), set())
