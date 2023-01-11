import json
import operator
from collections import defaultdict
from functools import cache, cached_property
from datetime import datetime, timedelta
import isodate

from peewee import prefetch, fn

from src.db.workout import models
from swagger_server.models.equipment_type import EquipmentType as APIEquipmentType


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
            equip_query = self._build_equipment_query(query.equipment)
            if equip_query is not None:
                wrkouts = wrkouts.where(models.Workouts.id << equip_query)

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
                query.in_hr_zone,
                "max_time",
                timedelta(seconds=0),
                isodate.parse_duration,
                operator.le,
                models.HRZones.duration,
                False,
            )

        if query.above_hr_zone is not None and len(query.above_hr_zone) > 0:
            quer = self._build_hr_zones_query(
                query.above_hr_zone,
                "percent_spent_above",
                -1,
                float,
                operator.ge,
                models.HRZones.percentspentabove,
                True,
            )
            if hr_zones_query is not None:
                hr_zones_query.union(quer)
            else:
                hr_zones_query = quer

        if hr_zones_query is not None:
            wrkouts = wrkouts.where(models.Workouts.id << hr_zones_query)

        return wrkouts

    def _build_hr_zones_query(
        self,
        query,
        second_name,
        second_default,
        second_type,
        second_comparison,
        second_model_field,
        second_exclusive,
    ):
        zones = defaultdict(dict)

        defaults = {
            "min_time": timedelta(days=1),
            second_name: second_default,
        }

        def check_replace(instance, field, cast_func, comparison_func):
            val = getattr(instance, field)
            if val is None:
                return
            new_val = cast_func(val)

            if comparison_func(
                new_val, zones[instance.zone_type].get(field, defaults[field]),
            ):
                zones[instance.zone_type][field] = new_val

        # combine any duplicates using lowest/highest values for each zone type
        for r in query:
            check_replace(r, second_name, second_type, operator.ge)
            check_replace(r, "min_time", isodate.parse_duration, operator.le)

        if len(zones) == 0:
            return None

        hr = models.HRZones.select(models.HRZones.workout_id)
        count = 0
        for k, v in zones.items():
            exp = models.HRZones.zonetype == k
            skip = False
            if second_name in v:
                exp &= second_comparison(second_model_field, v[second_name])
                if second_exclusive:
                    skip = True
            if not skip and "min_time" in v:
                exp &= models.HRZones.duration >= v["min_time"]
            count += 1
            hr = hr.orwhere(exp)
        hr = hr.group_by(models.HRZones.workout_id).having(
            fn.COUNT(models.HRZones.workout_id) == count
        )

        if hr._where is None:
            # If we have no valid search params, don't bother adding the clause
            return None

        return hr

    def _no_equipment_query(self):
        through = models.Workouts.equipment.get_through_model()
        return models.Workouts.select(models.Workouts.id).where(
            ~fn.EXISTS(through.select().where(through.workouts == models.Workouts.id))
        )

    def _api_enum_vals(self, api_enum):
        return set(
            v
            for k, v in api_enum.__dict__.items()
            if k[0:2] != "__" and not callable(v)
        )

    def _build_equipment_query(self, query):
        through = models.Workouts.equipment.get_through_model()
        equipment = (
            through.select(through.workouts)
            .join(models.Equipment)
            .group_by(through.workouts)
        )
        base = equipment

        equipment_types = set()
        ids = set()
        has_no_equip = False
        for e in query:
            if e.id is not None:
                ids.add(e.id)
                continue
            if e.equipment_type is None:
                continue
            if e.equipment_type == APIEquipmentType.NONE:
                has_no_equip = True
                continue
            if e.magnitude is None and e.quantity is None:
                equipment_types.add(e.equipment_type)
                continue

            exp = models.Equipment.equipmenttype == e.equipment_type
            if e.magnitude is not None:
                exp &= models.Equipment.magnitude == e.magnitude
            if e.quantity is not None:
                exp &= models.Equipment.quantity == e.quantity

            equipment = equipment.orwhere(exp)

        if len(ids) > 0:
            equipment = equipment.orwhere(models.Equipment.id << ids)
        if len(equipment_types) > 0:
            equipment = equipment.orwhere(
                models.Equipment.equipmenttype << equipment_types
            )
        if has_no_equip:
            if equipment._where is None:
                equipment = self._no_equipment_query()
            else:
                equipment = equipment.union(self._no_equipment_query())

        if equipment._where is None and (
            not hasattr(equipment, "op") or equipment.op != "UNION"
        ):
            # no valid search params added, don't bother adding a search clause
            # we need to check whether there's a union happening because this masks the where clauses
            return None

        return equipment

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
            srcs = srcs.where(
                models.Sources.length <= timedelta(seconds=query.length_max)
            )

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
            getattr(self.full_query, f"{i}_attributes")
            for i in self._query_ordering(self.model.__name__)
        ]
        self.logger.info("Starting query", model=name1, query=str(self.full_query))

        one = None
        if q1 is not None:
            one = getattr(self, f"_gen_{name1}_query")(q1)

        if q2 is not None:
            through = getattr(self.model, f"{name2}").get_through_model()
            two = (
                through.select(getattr(through, f"{name1}_id"))
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
            self.logger.info("Generated DB query", db_query=str(quer))
            return quer

        self.logger.info("No valid DB query")
        return None
