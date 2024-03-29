import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from functools import cache, cached_property

import isodate
import structlog
from overrides import override

import src.db.workout.models as models
from src.db.workout.db_interface import DBInterface
from src.db.workout.source import Source


class WorkoutBase(DBInterface):
    def _create_source(self, url):
        try:
            src = Source.load_source(self.db, url, self.logger)
            return src.insert_row()
        except Exception as e:
            self.logger.warn("Failed to insert source", url=Source.normalise_url(url))
            raise e

    @override
    def insert_row(self):
        pass


class ExistingWorkout(WorkoutBase):
    def __init__(self, db, starttime, logger):
        super().__init__(db, logger)
        self.model = self._populate_model(starttime)

    def _populate_model(self, starttime):
        return Workout.find(
            self.db, models.Workouts, models.Workouts.starttime, starttime
        )

    def add_sources(self, urls):
        if self.model is None:
            raise Exception("Model must be created before adding sources")
        new_sources = set()
        for url in urls:
            new_sources.add(self._create_source(url))

        model_sources = set(self.model.sources)
        new_sources -= model_sources

        with self.db.atomic():
            self.model.sources.add(list(new_sources))
            self.model.save()
        return new_sources

    @override
    def insert_row(self):
        return self.model


class Workout(WorkoutBase):
    def __init__(self, db, data, logger):
        super().__init__(db, logger)
        self._data = data
        self.logger = logger.bind(workout=self._data.log_abridged())

    def _populate_model(self):
        workout_model = models.Workouts(
            calories=self._data.calories,
            endtime=self._data.end_time,
            starttime=self._data.start_time,
            sport=self._data.sport,
            samples=self._data.samples,
        )
        for k, v in self._data.heart_rate_range.items():
            setattr(workout_model, f"{k}hr", v)

        self._add_hr_zones(workout_model)

        return workout_model

    @cached_property
    def data(self):
        return self._data

    @cached_property
    def equipment(self):
        equipment = []
        if len(self._data.equipment) == 0:
            return equipment

        with self.db.atomic():
            for k, v in self._data.equipment.items():
                for vals in v:
                    equip, created = models.Equipment.get_or_create(
                        equipmenttype=k,
                        magnitude=vals["magnitude"],
                        quantity=vals["quantity"],
                    )
                    if created:
                        self.logger.info(
                            "New equipment type inserted",
                            equipment=equip.as_dict(),
                            action="new",
                        )
                    equipment.append(equip)

        return equipment

    @override
    def insert_row(self):
        if (
            self._data.start_time is None
            or self._data.samples is None
            or len(self._data.samples) == 0
        ):
            # Not much we can do with this, skip it
            self.logger.warn("Invalid workout, exiting")
            return None
        wkout = self.find(
            self.db, models.Workouts, models.Workouts.starttime, self._data.start_time
        )
        if wkout is not None:
            self.logger.debug("Workout already in db; exiting")
            self.model = wkout
            return wkout

        self.model = self._populate_model()

        try:
            equipment = self.equipment
            tag_models = set()
            tag_models.update(
                set(self._insert_tags([self._data.sport,], models.TagType.SPORT,))
            )
            tags = self._equipment_to_tags()
            if len(tags) > 0:
                tag_models.update(
                    set(self._insert_tags(tags, models.TagType.EQUIPMENT))
                )

            self.sources = set()
            for url in self._data.sources:
                self.sources.add(self._create_source(url))

            self.logger.info("Inserted sources")

            with self.db.atomic():
                self.model.save()

                self.model.sources.add(list(self.sources))
                self.model.equipment.add(equipment)
                self.model.tags.add(list(tag_models))
                self.model.save()

        except Exception as e:
            self.logger.exception(
                "Failed to insert workout", start_time=self._data.start_time,
            )
            raise e

    @cache
    def _equipment_to_tags(self):
        tags = set()
        has_weights = False
        has_bands = False
        for e in self.equipment:
            if e.equipmenttype == models.EquipmentType.WEIGHTS:
                tags.add(f"{e.magnitude}lbs")
                has_weights = True
            elif e.equipmenttype == models.EquipmentType.BANDS:
                tags.add(f"{e.magnitude} band")
                has_bands = True

        if has_weights:
            tags.add("weights")
        if has_bands:
            tags.add("mini-band")

        return tags

    def _add_hr_zones(self, model):
        zone_data = self._data.hr_zones
        if len(zone_data) != 5:
            self.logger.warn("Invalid zone data found", zones=zone_data)
            return

        zone_names = ["below_50", "50_60", "60_70", "70_80", "80_90", "90_100"]

        full_duration = self._data.duration

        zones = []
        zero_time = timedelta(seconds=0)
        summed_duration = zero_time

        srt = lambda x: x["index"]
        for index, val in enumerate(sorted(zone_data, key=srt, reverse=True)):
            dur = isodate.parse_duration(val["in_zone"])
            summed_duration += dur
            spent_above = summed_duration / full_duration * 100
            prefix = f"zone_{zone_names[val['index']]}_"
            setattr(model, prefix + "lower", val["lower_limit"])
            setattr(model, prefix + "upper", val["upper_limit"])
            setattr(model, prefix + "duration", dur)
            setattr(model, prefix + "percentspentabove", spent_above)

        dur = full_duration - summed_duration

        prefix = f"zone_below_50_"
        setattr(model, prefix + "lower", 0)
        setattr(model, prefix + "upper", model.zone_50_60_lower)
        setattr(model, prefix + "duration", dur)
        setattr(model, prefix + "percentspentabove", 100)
