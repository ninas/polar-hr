import json
import unittest
from collections import defaultdict
from copy import deepcopy
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import src.db.workout.models as models
from src.db.workout.workout import Workout
from src.db.workout.workout_data_store import WorkoutDataStore
from src.utils.test_base import TestBase


class TestWorkout(TestBase):
    def setUp(self):
        self.db = MagicMock()
        self.raw_data = self.data()
        self.data = WorkoutDataStore(self.raw_data)
        self.workout = Workout(self.db, self.data, self.logger)
        self.workout.equipment = self._mock_equipment()
        self.workout._insert_tags = MagicMock(side_effect=lambda a, b: a)
        Workout._find = MagicMock(return_value=None)

    def data(self):
        with open("src/db/workout/tests/sample_data.json") as f:
            return json.loads(f.read())

    def test_exit_early(self):
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
        Workout._find = MagicMock(return_value="something")

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

    def test_tags_created(self):
        tgs = MagicMock()
        self.workout._populate_model = MagicMock(
            return_value=MagicMock(tags=MagicMock(add=tgs))
        )
        self.data._i_data["sources"] = []
        self.workout._insert_samples = MagicMock()
        self.workout._insert_hr_zones = MagicMock()
        self.workout.insert_row()
        self.assertEqual(
            set(*(tgs.call_args.args)), {"hiit", "5lbs", "8lbs", "weights",}
        )

    def test_equipment_to_tags(self):
        self.assertEqual(
            self.workout._equipment_to_tags(), {"5lbs", "8lbs", "weights",}
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

    def test_create_hr_zones(self):
        self.workout.model = MagicMock()
        self.data._i_data["duration"] = "PT100S"
        with patch("src.db.workout.workout.models.HRZones") as hrzones:
            zones = self.workout._insert_hr_zones()

        self.assertEqual(
            zones[0],
            {
                "zonetype": models.ZoneType.NINETY_100,
                "lowerlimit": 185,
                "higherlimit": 206,
                "duration": timedelta(seconds=10),
                "percentspentabove": 10,
                "workout": self.workout.model,
            },
        )
        self.assertEqual(
            zones[-1],
            {
                "zonetype": models.ZoneType.BELOW_50,
                "lowerlimit": 0,
                "higherlimit": 103,
                "duration": timedelta(seconds=10),
                "percentspentabove": 100,
                "workout": self.workout.model,
            },
        )
