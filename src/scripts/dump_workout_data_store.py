from collections import defaultdict
from functools import cache, cached_property

from typing import override

from src.db.workout import models
from src.db.workout.workout_data_store import WorkoutDataStore
from src.utils.equipment_parsing_mixin import EquipmentParsingMixin


class WorkoutDataWithFilenameStore(WorkoutDataStore):
    def __init__(self, input_data, filename):
        super().__init__(input_data)
        self.filename = filename

    @override
    def as_dict(self):
        d = super().as_dict()
        d["filename"] = self.filename
        return d


class DumpWorkoutDataStore(WorkoutDataWithFilenameStore, EquipmentParsingMixin):
    def __init__(self, input_data, filename):
        super().__init__(input_data, filename)
        self._sources = []
        self._equipment = defaultdict(list)
        self.has_original_note = "note" in self._i_data
        self._note = self._parse_original_note()

    @cached_property
    @override
    def start_time(self):
        return self.get_datetime("startTime")

    @cached_property
    @override
    def end_time(self):
        return self.get_datetime("stopTime")

    @cached_property
    @override
    def sport(self):
        self._i_data["sport"] = self._i_data.get(
            "name", self._i_data["exercises"][0].get("sport", "Unknown")
        )
        return super().sport

    @property
    @override
    def calories(self):
        return int(self._i_data.get("kiloCalories", 0))

    @cached_property
    @override
    def heart_rate_range(self):
        self._i_data["heart_rate"] = self._i_data["exercises"][0].get("heartRate", None)
        return super().heart_rate_range

    @cached_property
    @override
    def hr_zones(self):
        # their stuff is so inconsistent
        hr = (
            "heartRate"
            if "heartRate" in self._i_data["exercises"][0]["zones"]
            else "heart_rate"
        )
        to_return = []
        for zone in self._i_data["exercises"][0]["zones"][hr]:
            to_return.append(
                {
                    "upper_limit": zone["higherLimit"],
                    "lower_limit": zone["lowerLimit"],
                    "in_zone": zone["inZone"],
                    "index": zone["zoneIndex"],
                }
            )
        return to_return

    @property
    @override
    def note(self):
        if self._note is not None:
            return self._note
        if self.has_original_note:
            self._note = self._parse_original_note()
        return self._note

    @property
    @override
    def sources(self):
        return self._sources

    @property
    @override
    def equipment(self):
        return self._equipment

    @cached_property
    @override
    def samples(self):
        data = []
        for i in self._i_data["exercises"][0]["samples"]["heartRate"]:
            data.append(i.get("value", 0))
        return data

    @cached_property
    @override
    def _timezone_offset(self):
        return self._i_data.get("timeZoneOffset", -420)

    @cache
    def _parse_original_note(self):
        data = self._i_data.get("note", None)
        if data is None or len(data) == 0:
            return None

        note = None
        components = data.split(";")

        if components[0].startswith("Multiple"):
            divider = components[0].find(":")
            latter = components[0][divider + 1 :]
            self._sources = [i.strip() for i in latter.split(",")]
        else:
            self._sources.append(components[0].strip())

        index = 1
        while index < len(components):
            v = components[index].split(":")
            if len(v) == 1:
                index += 1
                continue
            title, rest = v

            if "weight" in title:
                self._equipment[models.EquipmentType.WEIGHTS] = self._extract_weights(
                    rest
                )
            elif "band" in title:
                self._equipment[models.EquipmentType.BANDS] = self._extract_bands(rest)
            elif title == "note" or title == "notes":
                self._note = rest

            index += 1

        return note
