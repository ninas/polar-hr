import sys
from functools import cached_property, cache
from collections import defaultdict
from overrides import override

from src.db.workout.workout_data_store import WorkoutDataStore
from src.db.workout import models


    def __init__(self, input_data):
        self._i_data = input_data
        self._sources = set()
        self._equipment = defaultdict(list)
        self._note = None

    def add_source(self, src):
        self._sources = set(src.sources.split(","))
        if src.notes is not None:
            self._note = src.notes

        if src.weights is not None:
            self._equipment[models.EquipmentType.WEIGHTS] = self._extract_weights(src.weights)

        if src.bands is not None:
            self._equipment[models.EquipmentType.BANDS] = self._extract_bands(src.bands)

    @property
    @override
    def sources(self):
        return list(self._sources)

    @property
    @override
    def equipment(self):
        return self._equipment

    @cached_property
    @override(check_signature=False)
    def end_time(self):
        return self.start_time + self.duration

    @property
    @override
    def note(self):
        return self._note

    @cached_property
    @override(check_signature=False)
    def sport(self):
        self._i_data["sport"] = self._i_data.get("detailed_sport_info", "unknown")
        return super().sport

    @cached_property
    @override(check_signature=False)
    def heart_rate_range(self):
        if "heart_rate" not in self._i_data or self._i_data["heart_rate"] is None:
            return super().heart_rate_range

        self._i_data["heart_rate"]["min"] = self._lowest_sample()
        for k, v in [("maximum", "max"), ("average", "avg")]:
            self._i_data["heart_rate"][v] = self._i_data["heart_rate"].get(k, 0)

        return super().heart_rate_range

    @cached_property
    @override(check_signature=False)
    def samples(self):
        return [int(i) for i in self._i_data["samples"][0]["data"].split(",")]

    @cache
    def _lowest_sample(self):
        m = sys.maxsize
        for i in self.samples:
            if i != 0 and i < m:
                m = i
        if m == sys.maxsize:
            return 0
        return m

    def _extract_bands(self, val):
        bands = []
        for i in filter(None, val.split(",")):
            bands.append(
                {"quantity": 1, "magnitude": i.strip()}
            )
        return bands

    def _extract_weights(self, val):
        equipment = []
        for i in filter(None, val.split(",")):
            dd = {"quantity": 2}
            i = i.strip()

            if i.startswith("one"):
                dd["quantity"] = 1
                i = i[3:].strip()

            dd["magnitude"] = i.strip()
            equipment.append(dd)
        return equipment
