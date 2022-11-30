import os, json, pprint, isodate
from datetime import datetime, timezone, timedelta
from functools import cached_property, cache
from collections import defaultdict
from overrides import EnforceOverrides


class WorkoutData(EnforceOverrides):
    def __init__(self, input_data):
        self._i_data = input_data

    @property
    def start_time(self):
        return self.get_datetime("start_time")

    @cached_property
    def duration(self):
        return isodate.parse_duration(self._i_data.get("duration", "PT0S"))

    @property
    def end_time(self):
        return self.get_datetime("end_time")

    @cached_property
    def sport(self):
        sport = self._i_data.get("sport", "unknown")
        # For some reason Polar subs these two
        if sport == "CROSS_FIT":
            sport = "HIIT"
        if sport == "STRENGTH_TRAINING":
            sport = "STRENGTH"
        return sport.lower().replace("_", " ")

    @property
    def calories(self):
        return int(self._i_data.get("calories", 0))

    @cached_property
    def heart_rate_range(self):
        if "heart_rate" not in self._i_data or self._i_data["heart_rate"] is None:
            return {"min": 0, "max": 0, "avg": 0}

        hr_data = {}
        for i in ["min", "max", "avg"]:
            hr_data[i] = int(self._i_data["heart_rate"].get(i, 0))

        return hr_data

    @property
    def note(self):
        return self._i_data.get("note", None)

    @property
    def hr_zones(self):
        return self._i_data.get("hr_zones", None)

    @property
    def samples(self):
        return self._i_data.get("samples", [])

    @property
    def sources(self):
        return self._i_data.get("sources", [])

    @property
    def equipment(self):
        return self._i_data.get("equipment", {})

    @property
    def _timezone_offset(self):
        return self._i_data.get("start_time_utc_offset", -420)


    def get_datetime(self, field, tz=None):
        dt = datetime.min
        if field in self._i_data:
            dt = datetime.fromisoformat(self._i_data[field])

        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            # We need to add timezone
            if tz is None:
                tz = self._timezone_offset
            dt = datetime.fromisoformat(f"{dt}{tz/60:+03.0f}:00")

        return dt.astimezone(
            timezone.utc
        )

    @cache
    def as_dict(self):
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration": isodate.duration_isoformat(self.duration),
            "sport": self.sport,
            "calories": self.calories,
            "heart_rate": self.heart_rate_range,
            "hr_zones": self.hr_zones,
            "samples": self.samples,
            "note": self.note,
            "sources": self.sources,
            "equipment": self.equipment
        }
