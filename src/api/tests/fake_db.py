import unittest
import json
from datetime import timedelta, datetime
from functools import cache

from src.utils import log
from src.utils.test_base import TestBase
from src.api.complex_query import ComplexQuery
from src.db.workout import models


def insert_data(db):
    sources = _gen_sources(db)
    equipment = _gen_equipment(db)
    workouts = _gen_workouts(db, sources, equipment)


def _flatten_tags(tags):
    t = []
    for k, v in tags.items():
        t.extend(v)
    return t


def _gen_sources(db):
    sources = []
    with db.atomic():
        # source 1
        tags = {
            models.TagType.TAG: ["tag1", "tag2"],
            models.TagType.EXERCISE: ["exercise1", "exercise2", "exercise3"],
            models.TagType.CREATOR: ["creator1"],
        }
        _insert_tags(db, tags)
        sources.append(
            models.Sources.create(
                name="source 1 name",
                creator="creator1",
                url="https://youtube.com/source1",
                sourcetype=models.SourceType.YOUTUBE,
                length=timedelta(minutes=25),
            )
        )
        sources[-1].tags.add(
            models.Tags.select().where(models.Tags.name << _flatten_tags(tags))
        )

        # source 2
        tags = {
            models.TagType.TAG: ["tag2", "tag3", "tag4"],
            models.TagType.EXERCISE: ["exercise3", "exercise4", "exercise5"],
            models.TagType.CREATOR: ["creator1"],
        }
        _insert_tags(db, tags)
        sources.append(
            models.Sources.create(
                name="source 2 name",
                creator="creator1",
                url="https://youtube.com/source2",
                sourcetype=models.SourceType.YOUTUBE,
                length=timedelta(minutes=35),
            )
        )
        sources[-1].tags.add(
            models.Tags.select().where(models.Tags.name << _flatten_tags(tags))
        )

        # source 3
        tags = {
            models.TagType.TAG: ["tag2", "tag4", "tag5", "tag6"],
            models.TagType.EXERCISE: [
                "exercise1",
                "exercise3",
                "exercise6",
                "exercise7",
            ],
            models.TagType.CREATOR: ["creator2"],
        }
        _insert_tags(db, tags)
        sources.append(
            models.Sources.create(
                name="source 3 name",
                creator="creator2",
                url="https://youtube.com/source3",
                sourcetype=models.SourceType.YOUTUBE,
                length=timedelta(minutes=30),
            )
        )
        sources[-1].tags.add(
            models.Tags.select().where(models.Tags.name << _flatten_tags(tags))
        )

        return sources


def _gen_workouts(db, sources, equipment):
    workouts = []
    with db.atomic():
        # workout 1
        _insert_tags(db, {models.TagType.SPORT: ["sport1"]})
        tags = models.Tags.select().where(
            models.Tags.name << ["5lbs", "8lbs", "sport1"]
        )
        workouts.append(
            models.Workouts.create(
                avghr=150,
                calories=200,
                endtime=datetime(2022, 10, 10, 10, 25),
                maxhr=180,
                minhr=100,
                notes="some note",
                sport="sport1",
                starttime=datetime(2022, 10, 10, 10, 0),
            )
        )
        workouts[-1].equipment.add(
            [equipment["weights"]["5"], equipment["weights"]["8"]]
        )
        workouts[-1].sources.add([sources[0]])
        workouts[-1].tags.add(tags)
        models.Samples.create(
            samples=json.dumps({"somedata": "something"}), workout=workouts[-1]
        )
        # percent above: [100, 100, 96, 76, 36, 4]
        _insert_hr_zones(db, [0, 1, 5, 10, 8, 1], workouts[-1], 200)

        # workout 2, same source
        tags = models.Tags.select().where(
            models.Tags.name << ["5lbs", "8lbs", "10lbs", "sport1"]
        )
        workouts.append(
            models.Workouts.create(
                avghr=160,
                calories=200,
                endtime=datetime(2022, 10, 11, 10, 25),
                maxhr=190,
                minhr=100,
                notes="some note",
                sport="sport1",
                starttime=datetime(2022, 10, 11, 10, 0),
            )
        )
        workouts[-1].equipment.add(
            [
                equipment["weights"]["5"],
                equipment["weights"]["8"],
                equipment["weights"]["10"],
            ]
        )
        workouts[-1].sources.add([sources[0]])
        workouts[-1].tags.add(tags)

        models.Samples.create(
            samples=json.dumps({"somedata": "something"}), workout=workouts[-1]
        )
        # percent above: [100, 100, 92, 72, 60, 20]
        _insert_hr_zones(db, [0, 2, 5, 3, 10, 5], workouts[-1], 200)

        # workout 3
        _insert_tags(db, {models.TagType.SPORT: ["sport2"]})
        tags = models.Tags.select().where(models.Tags.name << ["sport2"])
        workouts.append(
            models.Workouts.create(
                avghr=130,
                calories=200,
                endtime=datetime(2022, 10, 12, 10, 35),
                equipment=[],
                maxhr=159,
                minhr=120,
                notes="some note",
                sport="sport2",
                starttime=datetime(2022, 10, 12, 10, 0),
            )
        )
        workouts[-1].sources.add([sources[1]])
        workouts[-1].tags.add(tags)
        models.Samples.create(
            samples=json.dumps({"somedata": "something"}), workout=workouts[-1]
        )
        # percent above: [100, 100, 100, 60, 0, 0]
        _insert_hr_zones(db, [0, 0, 20, 15, 0, 0], workouts[-1], 200)

        # workout 4
        tags = models.Tags.select().where(
            models.Tags.name << ["sport1", "medium band", "8lbs"]
        )
        workouts.append(
            models.Workouts.create(
                avghr=130,
                calories=200,
                endtime=datetime(2022, 10, 13, 10, 32),
                equipment=[],
                maxhr=185,
                minhr=80,
                notes="some note",
                sport="sport1",
                starttime=datetime(2022, 10, 13, 10, 0),
            )
        )
        workouts[-1].equipment.add(
            [equipment["bands"]["medium"], equipment["weights"]["8"]]
        )
        workouts[-1].sources.add([sources[2]])
        workouts[-1].tags.add(tags)
        models.Samples.create(
            samples=json.dumps({"somedata": "something"}), workout=workouts[-1]
        )
        # percent above: [100, 86, 71, 43, 29, 14]
        _insert_hr_zones(db, [5, 5, 5, 10, 5, 5], workouts[-1], 200)


def _insert_hr_zones(db, durations, workout, max_hr):
    total = sum(durations)
    interval = int(max_hr / 10)
    half = int(max_hr / 2)
    vals = [
        [models.ZoneType.BELOW_50, 0],
        [models.ZoneType.FIFTY_60, half],
        [models.ZoneType.SIXTY_70, half + interval],
        [models.ZoneType.SEVENTY_80, half + interval * 2],
        [models.ZoneType.EIGHTY_90, half + interval * 3],
        [models.ZoneType.NINETY_100, half + interval * 4],
    ]

    with db.atomic():
        for i, v in enumerate(vals):
            name, start = v
            end = vals[i + 1][1] - 1 if i + 1 < len(vals) else max_hr
            models.HRZones.create(
                zonetype=name,
                lowerlimit=start,
                higherlimit=end,
                duration=timedelta(minutes=durations[i]),
                percentspentabove=durations[i] / total * 100,
                workout=workout,
            )


def _gen_equipment(db):
    equipment = {"weights": {}, "bands": {}}
    with db.atomic():
        for i in ["5", "8", "10"]:
            equipment["weights"][i] = models.Equipment.create(
                equipmenttype=models.EquipmentType.WEIGHTS, magnitude=i, quantity=2
            )
        equipment["bands"]["medium"] = models.Equipment.create(
            equipmenttype=models.EquipmentType.BANDS, magnitude="medium"
        )

        _insert_tags(
            db, {models.TagType.EQUIPMENT: ["5lbs", "8lbs", "10lbs", "medium band"]}
        )

    return equipment


def _insert_tags(db, tags):
    with db.atomic():
        for k, v in tags.items():
            models.Tags.insert_many(
                [{"name": i, "tagtype": k} for i in v]
            ).on_conflict_ignore().execute()
