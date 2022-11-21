import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock
from datetime import timedelta
from collections import defaultdict

from workout import Workout
import db.models as models


class TestWorkout(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.data = self.data()
        self.workout = Workout(self.db, self.data)
        self.workout._find = MagicMock(return_value=None)

    def data(self):
        return {
            "duration": "PT100S",
            "exercises": [
                {
                    "zones": {
                        "heart_rate": [
                            {
                                "lowerLimit": 103,
                                "higherLimit": 124,
                                "inZone": "PT10S",
                                "zoneIndex": 1,
                            },
                            {
                                "lowerLimit": 124,
                                "higherLimit": 144,
                                "inZone": "PT20S",
                                "zoneIndex": 2,
                            },
                            {
                                "lowerLimit": 144,
                                "higherLimit": 165,
                                "inZone": "PT30S",
                                "zoneIndex": 3,
                            },
                            {
                                "lowerLimit": 165,
                                "higherLimit": 185,
                                "inZone": "PT20S",
                                "zoneIndex": 4,
                            },
                            {
                                "lowerLimit": 185,
                                "higherLimit": 206,
                                "inZone": "PT10S",
                                "zoneIndex": 5,
                            },
                        ]
                    },
                    "samples": ["something"],
                }
            ],
        }

    def test_if_in_db_skip(self):
        # Let's mock this so we can see if it's reached
        self.workout._find.return_value = "something"
        self.workout._populate_model = MagicMock()
        self.workout._find = MagicMock(return_value="something")
        self.workout._populate_model.assert_not_called()

    @patch("workout.upload_to_cloud_storage")
    def test_fail_upload_blob(self, mock_cloud_storage):
        mock_cloud_storage.side_effect = Exception("something")
        self.assertRaises(Exception, self.workout.insert_row)

    @patch("workout.models.Workouts")
    @patch("workout.upload_to_cloud_storage")
    @patch("workout.Source.load_source")
    def test_failed_insert(self, mock_src, mock_cloud_store, mock_workout_model):

        self.workout.note_data = {"sources": ["something"]}
        self.workout._populate_model = MagicMock()
        # If we error inserting a row, print info and move on
        mock_cloud_store.return_value = "something"
        mock_src.side_effect = Exception("oops")

        try:
            self.workout.insert_row()
        except Exception as e:
            self.fail("Workout.insert_row raised an unexpected exception")

    def test_create_hr_zones(self):
        workout = MagicMock()
        with patch("workout.models.HRZones") as hrzones:
            zones = self.workout._create_hr_zones(workout)

        self.assertEqual(
            zones[0],
            {
                "zonetype": models.ZoneType.NINETY_100,
                "lowerlimit": 185,
                "higherlimit": 206,
                "duration": timedelta(seconds=10),
                "percentspentabove": 10,
                "workout": workout,
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
                "workout": workout,
            },
        )

    def test_equipment_gen(self):
        self.workout.note_data = {}
        self.assertEqual(self.workout.equipment, [])

        self.workout._equipment = None
        self.workout.note_data = {
            "equipment": {
                models.EquipmentType.WEIGHTS: [{"magnitude": "10", "quantity": 1}]
            }
        }

        with patch("workout.models.Equipment") as mock_equip:
            mock_equip.get_or_create = MagicMock(return_value=(MagicMock(), True))
            self.assertEqual(len(self.workout.equipment), 1)

    def test_parse_note(self):

        empty_dict = defaultdict(list)
        vid1 = "www.vid1.com"
        vid2 = "www.vid2.com"
        vid3 = "www.vid3.com"
        val_to_response = {
            "": {},
            None: {},
            f"Multiple videos: {vid1} , {vid2} , {vid3}": {
                "sources": [vid1, vid2, vid3],
                "equipment": empty_dict,
            },
            f"{vid1} ; weights: 1,2,3, one 4": {
                "sources": [vid1],
                "equipment": defaultdict(
                    list,
                    {
                        models.EquipmentType.WEIGHTS: [
                            {"quantity": 2, "magnitude": "1"},
                            {"quantity": 2, "magnitude": "2"},
                            {"quantity": 2, "magnitude": "3"},
                            {"quantity": 1, "magnitude": "4"},
                        ]
                    },
                ),
            },
            f"{vid1} ; weights:": {"sources": [vid1], "equipment": empty_dict},
            f"Multiple videos: {vid1} , {vid2} ; bands: medium,heavy ; note: nothing": {
                "sources": [vid1, vid2],
                "equipment": defaultdict(
                    list,
                    {
                        models.EquipmentType.BANDS: [
                            {"quantity": 1, "magnitude": "medium"},
                            {"quantity": 1, "magnitude": "heavy"},
                        ]
                    },
                ),
            },
        }

        for k, v in val_to_response.items():
            self.assertEqual(self.workout._parse_note(k), v)
