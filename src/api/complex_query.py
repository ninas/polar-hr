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
    def __init__(self, logger=None, is_dev=False):
        self.logger = logger

    def _in_or_equal(self, field, vals):
        if len(vals) > 1:
            return field << set(vals)
        return field == vals.pop()

    def _gen_workouts_query(self, query, wrkouts=None):
        if wrkouts is None:
            wrkouts = models.Workouts.select(models.Workouts.id)
        wrk_model = wrkouts.model
        expressions = None

        if query.sport is not None and len(query.sport) > 0:

            wrkouts = wrkouts.where(self._in_or_equal(wrk_model.sport, query.sport))

        if query.equipment is not None and len(query.equipment) > 0:
            equip_query = self._build_equipment_query(query.equipment)
            if equip_query is not None:
                wrkouts = wrkouts.where(wrk_model.id << equip_query)

        if query.hr_range is not None:
            if query.hr_range.min is not None:
                wrkouts = wrkouts.where(wrk_model.minhr >= query.hr_range.min)
            if query.hr_range.max is not None:
                wrkouts = wrkouts.where(wrk_model.maxhr <= query.hr_range.max)

        if query.avg_hr_range is not None:
            if query.avg_hr_range.min is not None:
                wrkouts = wrkouts.where(wrk_model.avghr >= query.avg_hr_range.min)
            if query.avg_hr_range.max is not None:
                wrkouts = wrkouts.where(wrk_model.avghr <= query.avg_hr_range.max)
        if query.in_hr_zone is not None and len(query.in_hr_zone) > 0:
            wrkouts = self._build_hr_zones_query(
                query.in_hr_zone,
                "max_time",
                timedelta(seconds=0),
                isodate.parse_duration,
                operator.le,
                "duration",
                False,
                wrkouts,
            )

        if query.above_hr_zone is not None and len(query.above_hr_zone) > 0:
            wrkouts = self._build_hr_zones_query(
                query.above_hr_zone,
                "percent_spent_above",
                -1,
                float,
                operator.ge,
                "percentspentabove",
                True,
                wrkouts,
            )

        if wrkouts._where is None:
            return None
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
        model_select,
    ):
        hr_model = model_select.model
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

        hr = model_select
        count = 0
        for k, v in zones.items():
            field_name_prefix = f"zone_{k}_"
            skip = False
            exp = None
            if second_name in v:
                exp = second_comparison(
                    getattr(hr_model, field_name_prefix + second_model_field),
                    v[second_name],
                )
                if second_exclusive:
                    skip = True
            if not skip and "min_time" in v:
                exp2 = (
                    getattr(hr_model, field_name_prefix + "duration") >= v["min_time"]
                )
                if exp is None:
                    exp = exp2
                else:
                    exp &= exp2

            count += 1
            if exp is not None:
                hr = hr.where(exp)

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
            equipment = equipment.orwhere(self._in_or_equal(models.Equipment.id, ids))
        if len(equipment_types) > 0:
            equipment = equipment.orwhere(
                self._in_or_equal(models.Equipment.equipmenttype, equipment_types)
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

    def _gen_sources_query(self, query, srcs=None):
        if srcs is None:
            srcs = models.Sources.select(models.Sources.id)
        src_model = srcs.model
        source_tags_to_filter = set()

        if query.creator is not None:
            srcs = srcs.where(src_model.creator == query.creator)

        if query.length_min is not None:
            srcs = srcs.where(src_model.length >= timedelta(seconds=query.length_min))
        if query.length_max is not None:
            srcs = srcs.where(src_model.length <= timedelta(seconds=query.length_max))

        if query.source_type is not None:
            srcs = srcs.where(src_model.sourcettype == query.source_type)

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
            srcs = srcs.where(src_model.id << sub_query)

        if srcs._where is None:
            return None

        return srcs

    @cache
    def _query_ordering(self, model_name):
        return {
            "SourcesMaterialized": ["sources", "workouts"],
            "WorkoutsMaterialized": ["workouts", "sources"],
        }[model_name]

    @cache
    def _materialized_source(self, name):
        return {"sources": models.Sources, "workouts": models.Workouts,}[name]

    def execute(self, query, model):
        name1, name2 = self._query_ordering(model.__name__)
        q1, q2 = [
            getattr(query, f"{i}_attributes")
            for i in self._query_ordering(model.__name__)
        ]
        self.logger.info("Starting query", model=name1, query=str(query))
        mm_select = model.select()
        if model.__name__ == "WorkoutsMaterialized" and not q1.samples:
            self.logger.debug("Excluding samples")
            mm_select = self._exclude_samples()

        one = None
        if q1 is not None:
            one = getattr(self, f"_gen_{name1}_query")(q1, mm_select)

        if q2 is not None:
            through = getattr(
                self._materialized_source(name1), f"{name2}"
            ).get_through_model()
            genned = getattr(self, f"_gen_{name2}_query")(q2)
            if genned is not None:
                two = (
                    through.select(getattr(through, f"{name1}_id"))
                    .join(self._materialized_source(name1))
                    .where(getattr(through, f"{name2}_id") << genned)
                )
                if one is None:
                    one = mm_select
                one = one.where(model.id << two)

        if one is None or one._where is None:
            self.logger.info("No valid DB query")
            return None

        self.logger.info("Generated DB query", db_query=str(one))
        return one

    @cache
    def _exclude_samples(self):
        fields = []
        for name, field in models.WorkoutsMaterialized._meta.fields.items():
            if name != "samples":
                fields.append(field)
        return models.WorkoutsMaterialized.select(*fields)
