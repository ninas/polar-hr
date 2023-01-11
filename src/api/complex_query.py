import json
from functools import cache, cached_property
from datetime import datetime, timedelta
import isodate

from peewee import prefetch, fn

from src.db.workout import models


class ComplexQuery:
    def __init__(self, query, model, logger=None, is_dev=True):
        self.logger = logger
        self.full_query = query
        self.model = model

    def _gen_workouts_query(self, query):
        wrkouts = models.Workouts.select(models.Workouts.id)

        if query.sport is not None and len(query.sport) > 0:
            wrkouts = wrkouts.where(models.Workouts.sport << set(query.sport))

        if query.equipment is not None and len(query.equipment) > 0:
            wrkouts = wrkouts.where(
                models.Workouts.id << self._build_equipment_query(query.equipment)
            )
        if query.hr_range is not None:
            if query.hr_range.min is not None:
                wrkouts = wrkouts.where(models.Workouts.minhr >= query.hr_range.min)
            if query.hr_range.max is not None:
                wrkouts = wrkouts.where(models.Workouts.maxhr <= query.hr_range.max)

        if query.avg_hr_range is not None:
            if query.avg_hr_range.min is not None:
                wrkouts = wrkouts.where(models.Workouts.avghr >= query.avg_hr_range.min)
            if query.avg_hr_range.max is not None:
                wrkouts = wrkouts.where(models.Workouts.avghr <= query.avg_hr_range.max)
        hr_zones_query = None
        if query.in_hr_zone is not None and len(query.in_hr_zone) > 0:
            hr_zones_query = self._build_hr_zones_query(
                query.in_hr_zones, "percent_spent_in"
            )

        if query.above_hr_zone is not None and len(query.above_hr_zone) > 0:
            quer = self._build_hr_zones_query(query.in_hr_zones, "percent_spent_above")
            if hr_zones_query is not None:
                hr_zones_query.union(quer)
            else:
                hr_zones_query = quer

        if hr_zones_query is not None:
            wrkouts = wrkouts.where(models.Workouts.id << hr_zones_query)

        return wrkouts

    def _build_hr_zones_query(self, query, percent_field):
        zones = defaultdict(dict)

        defaults = {
            "min": timedelta(days=1),
            "max": timedelta(seconds=0),
            "percent": -1,
        }
        lt = lambda a, b: a < b
        gt = lambda a, b: a > b

        def check_replace(instance, new_field, saved_field, cast_func, comparison_func):
            if getattr(instance, new_field) is None:
                return
            new_val = cast_func(getattr(instance, new_field))

            if comparison_func(
                new_val,
                zones[instance.zone_type].get(saved_field, defaults[saved_field]),
            ):
                zones[instance.zone_type][saved_field] = new_val

        # combine any duplicates using lowest/highest values for each zone type
        for r in query:
            if getattr(r, percent_field) is not None:
                check_replace(r, percent_field, "percent", float, gt)
            if "percent" in zones:
                continue
            check_replace(r, "min_time", "min", isodate.parse_duration, lt)
            check_replace(r, "max_time", "max", isodate.parse_duration, gt)

        if len(zones) == 0:
            return None

        hr = models.HRZones.select(models.HRZones.workout)
        for k, v in zones.items():
            exp = models.HRZones.zonetype == k
            if "percent" in v:
                exp &= models.HRZones.percentspentabove >= v["percent"]
            else:
                if "min" in v:
                    exp &= models.HRZones.duration >= v["min"]
                if "max" in v:
                    exp &= models.HRZones.duration <= v["max"]
            hr = hr.orwhere(exp)
        return hr

    def _build_equipment_query(self, query):
        equipment = (
            models.Workouts.select(models.Workouts.id)
            .join(models.Workouts.equipment.get_through_model())
            .join(models.Equipment)
        )

        equipment_types = set()
        ids = set()
        for e in query:
            if e.id is not None:
                ids.add(e.id)
                continue
            if e.equipment_type is None:
                continue
            if e.magnitude is None and e.quantity is None:
                equipment_types.add(e.equipment_type)
                continue

            exp = models.Equipment.equipmenttype == e.equipment_type
            if e.magnitude is not None:
                exp &= models.Equipment.magnitude == e.magnitude
            if e.quantity is not None:
                exp &= models.Equipment.quantity == e.quantity

            equipment.orwhere(exp)

        if len(ids) > 0:
            equipment.orwhere(models.Equipment.id << ids)
        if len(equipment_types) > 0:
            equipment.orwhere(models.Equipment.equipmenttype << equipment_types)
        return equipment.group_by(models.Workouts.id)

    def _gen_sources_query(self, query):
        srcs = models.Sources.select(models.Sources.id)
        source_tags_to_filter = set()

        if query.creator is not None:
            srcs = srcs.where(models.Sources.creator == query.creator)

        if query.length_min is not None:
            srcs = srcs.where(
                models.Sources.length >= timedelta(seconds=query.length_min)
            )
        if query.length_max is not None:
            srcs = srcs.where(models.Sources.length <= timedelta(query.length_max))

        if query.source_type is not None:
            srcs = srcs.where(models.Sources.sourcettype == query.source_type)

        if query.exercises is not None:
            source_tags_to_filter.update(set(query.exercises))
        if query.tags is not None:
            source_tags_to_filter.update(set(query.tags))

        if len(source_tags_to_filter) > 0:
            sub_query = (
                models.Sources.select(models.Sources.id)
                .join(models.Sources.tags.get_through_model())
                .join(models.Tags)
                .where(models.Tags.name << source_tags_to_filter)
                .group_by(models.Sources.id)
                .having(fn.COUNT(models.Sources.id) == len(source_tags_to_filter))
            )
            srcs = srcs.where(models.Sources.id << sub_query)

        return srcs

    @cache
    def _query_ordering(self, model_name):
        return {
            "Sources": ["sources", "workouts"],
            "Workouts": ["workouts", "sources"],
        }[model_name]

    def execute(self):
        name1, name2 = self._query_ordering(self.model.__name__)
        q1, q2 = [
            getattr(self.query, f"{i}_attributes")
            for i in self._query_ordering(model.__name__)
        ]

        one = None
        if q1 is not None:
            one = getattr(self, f"_gen_{name1}_query")(q1)

        if q2 is not None:
            through = getattr(self.model, f"{name2}").get_through_model()
            two = (
                through.select(self.model.id)
                .join(self.model)
                .where(
                    getattr(through, f"{name2}_id")
                    << getattr(self, f"_gen_{name2}_query")(q2)
                )
            )
            if one is None:
                one = two
            else:
                one = one.intersect(two)

        if one is not None:
            select = self.model.select()
            if self.model.__name__ == "Workouts" and q1.samples:
                select = models.Workouts.select(
                    models.Workouts, models.Samples.samples
                ).join(
                    models.Samples,
                    on=(models.Samples.workout_id == models.Workouts.id),
                    attr="samples",
                )
            quer = select.where(self.model.id << one)
            return quer

        return None
