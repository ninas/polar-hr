from collections import defaultdict
import isodate, traceback
from .utils import upload_to_cloud_storage
from datetime import timedelta, datetime
from overrides import override

from .db_interface import DBInterface
from .source import Source
from db import models


class Workout(DBInterface):
    @override
    def __init__(self, db, data):
        super().__init__(db, data)
        self.hr_zones = None
        self._sources = None
        self._equipment = None
        self._sport = None
        self.start_time = self._val_or_none(["startTime"], datetime.fromisoformat)
        self.note_data = self._parse_note(self._val_or_none(["note"]))

    def _populate_model(self, data):
        workout_model = models.Workouts(
            calories=self._val_or_none(["kiloCalories"], int),
            endtime=self.end_time,
            starttime=self.start_time,
            sport=self.sport
        )
        path = ["exercises", 0, "heartRate"]
        workout_model.avghr = self._val_or_none(path + ["avg"], int)
        workout_model.maxhr = self._val_or_none(path + ["max"], int)
        workout_model.minhr = self._val_or_none(path + ["min"], int)

        return workout_model

    @property
    def sport(self):
        if self._sport is not None:
            return self._sport
        sport = self._val_or_none(["exercises", 0, "sport"])
        # For some reason Polar subs these two
        if sport == "CROSS_FIT":
            sport = "HIIT"
        if sport == "STRENGTH_TRAINING":
            sport = "STRENGTH"
        self._sport = sport.lower().replace("_", " ")
        return self._sport

    @property
    def samples(self):
        return self._val_or_none(["exercises", 0, "samples"])

    @property
    def end_time(self):
        return self._val_or_none(["stopTime"])

    @property
    def equipment(self):
        if self._equipment is not None:
            return self._equipment
        self._equipment = []
        if "equipment" not in self.note_data:
            return self._equipment

        with self.db.atomic():
            for k, v in self.note_data["equipment"].items():
                for vals in v:
                    equip, created = models.Equipment.get_or_create(
                        equipmenttype=k,
                        magnitude=vals["magnitude"],
                        quantity=vals["quantity"],
                    )
                    if created:
                        print(f"New equipment type inserted: {equip}")
                    self._equipment.append(equip)

        return self._equipment

    @override
    def insert_row(self):
        if self.start_time is None or self.samples is None:
            # Not much we can do with this, skip it
            return None
        wkout = self._find(
            self.db, models.Workouts, models.Workouts.starttime, self.start_time
        )
        if wkout is not None:
            return wkout

        self.model = self._populate_model(self.data)

        if self.samples is not None:
            # Let's put the sample in a blob store rather than the db
            # If this fails, we want to fail inserting the record, so let exception propagate
            samples_name = upload_to_cloud_storage(str(self.start_time), self.samples)
            self.model.samples = samples_name

        try:

            equipment = self.equipment
            tag_models = set()
            tag_models.update(set(self._insert_tags([self.sport,], models.TagType.SPORT)))
            tags = self._equipment_to_tags()
            if len(tags) > 0:
                tag_models.update(set(self._insert_tags(tags, models.TagType.EQUIPMENT)))

            self.sources = []
            if "sources" in self.note_data:
                for url in self.note_data["sources"]:
                    src = Source.load_source(self.db, url)
                    src.insert_row()
                    self.sources.append(src.model)


            with self.db.atomic():
                self.model.save()

                self.model.sources.add(self.sources)
                self.model.equipment.add(equipment)
                self.model.tags.add(list(tag_models))
                self.model.save()

            self.hr_zones = self._create_hr_zones(self.model)

        except Exception as e:
            print("Failed to insert workout:")
            print(
                f"\tFilename: {self.data['filename'] if 'filename' in self.data else 'None'}"
            )
            print(f"\tStart time: {self.start_time}")
            print(e)
            print(traceback.format_exc())

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


    def _create_hr_zones(self, workout_obj):
        zone_data = self._val_or_none(
            ["exercises", 0, "zones", "heart_rate"], data=self.data
        )
        if zone_data is None:
            print("No zone data found")
            return []

        zone_names = [
            models.ZoneType.NINETY_100,
            models.ZoneType.EIGHTY_90,
            models.ZoneType.SEVENTY_80,
            models.ZoneType.SIXTY_70,
            models.ZoneType.FIFTY_60,
        ]

        full_duration = isodate.parse_duration(self.data["duration"])

        zones = []
        zero_time = timedelta(seconds=0)
        summed_duration = zero_time

        srt = lambda x: x["zoneIndex"]
        for index, val in enumerate(sorted(zone_data, key=srt, reverse=True)):
            dur = isodate.parse_duration(val["inZone"])
            summed_duration += dur
            spent_above = summed_duration / full_duration * 100

            zones.append(
                {
                    "zonetype": zone_names[index],
                    "lowerlimit": val["lowerLimit"],
                    "higherlimit": val["higherLimit"],
                    "duration": dur,
                    "percentspentabove": spent_above,
                    "workout": workout_obj,
                }
            )

            index += 1

        dur = full_duration - summed_duration

        zones.append(
            {
                "zonetype": models.ZoneType.BELOW_50,
                "lowerlimit": 0,
                "higherlimit": zones[-1]["lowerlimit"],
                "duration": dur,
                "percentspentabove": 100,
                "workout": workout_obj,
            }
        )

        with self.db.atomic():
            models.HRZones.insert_many(zones).on_conflict_ignore().execute()

        return zones

    def _parse_note(self, data):
        if data is None or len(data) == 0:
            return {}

        attributes = {
            "sources": [],
            "equipment": defaultdict(list),
        }

        components = data.split(";")

        if components[0].startswith("Multiple"):
            divider = components[0].find(":")
            latter = components[0][divider + 1 :]
            attributes["sources"] = [i.strip() for i in latter.split(",")]
        else:
            attributes["sources"].append(components[0].strip())

        index = 1
        while index < len(components):
            v = components[index].split(":")
            if len(v) == 1:
                index += 1
                continue
            title, rest = v

            if "weight" in title:
                for i in filter(None, rest.split(",")):
                    dd = {"quantity": 2}
                    i = i.strip()

                    if i.startswith("one"):
                        dd["quantity"] = 1
                        i = i[3:].strip()

                    dd["magnitude"] = i.strip()
                    attributes["equipment"][models.EquipmentType.WEIGHTS].append(dd)
            elif "band" in title:
                for i in filter(None, rest.split(",")):
                    attributes["equipment"][models.EquipmentType.BANDS].append(
                        {"quantity": 1, "magnitude": i.strip()}
                    )
            elif title == "note" or title == "notes":
                attributes["note"] = rest

            index += 1

        return attributes
