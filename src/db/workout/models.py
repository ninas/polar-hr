from peewee import (
    TextField,
    IntegerField,
    ForeignKeyField,
    FloatField,
    TextField,
    ManyToManyField,
    CharField,
    SQL,
)
from playhouse.postgres_ext import (
    PostgresqlExtDatabase,
    JSONField,
    IntervalField,
    DateTimeTZField,
    BinaryJSONField,
)
from collections import defaultdict
from functools import cache

from src.db.base_model import BaseModel
from src.db.enum_field import EnumField, ExtendedEnum

database = PostgresqlExtDatabase(None, autorollback=True)

# types


class EquipmentType(ExtendedEnum):
    WEIGHTS = "weights"
    BANDS = "bands"


class SourceType(ExtendedEnum):
    YOUTUBE = "youtube"
    FITON = "fiton"
    UNKNOWN = "unknown"


class ZoneType(ExtendedEnum):
    BELOW_50 = "BELOW_FIFTY"
    FIFTY_60 = "FIFTY_60"
    SIXTY_70 = "SIXTY_70"
    SEVENTY_80 = "SEVENTY_80"
    EIGHTY_90 = "EIGHTY_90"
    NINETY_100 = "NINETY_100"


class TagType(ExtendedEnum):
    TAG = "TAG"
    EXERCISE = "EXERCISE"
    SPORT = "SPORT"
    CREATOR = "CREATOR"
    EQUIPMENT = "EQUIPMENT"


# tables


class WorkoutBaseModel(BaseModel):
    class Meta:
        database = database

    @classmethod
    def create_table(cls, *args, **kwargs):
        for field in cls._meta.fields.items():
            if type(field[1]) == EnumField:
                field[1].pre_field_create(cls)

        super().create_table(cls)

        for field in cls._meta.fields.items():
            if type(field[1]) == EnumField:
                field[1].post_field_create(cls)


class Tags(WorkoutBaseModel):
    name = TextField(unique=True)
    tagtype = EnumField(TagType, constraints=[SQL("DEFAULT 'TAG'")])


class Equipment(WorkoutBaseModel):
    equipmenttype = EnumField(EquipmentType)
    magnitude = TextField()
    quantity = IntegerField(constraints=[SQL("DEFAULT 1")], null=True)


class Sources(WorkoutBaseModel):
    extrainfo = JSONField(null=True)
    length = IntervalField(null=True)
    creator = TextField(null=True)
    name = TextField(null=True)
    sourcetype = EnumField(SourceType)
    url = TextField(unique=True)
    tags = ManyToManyField(Tags, backref="sources")


class Workouts(WorkoutBaseModel):
    avghr = IntegerField(null=True)
    calories = IntegerField(null=True)
    endtime = DateTimeTZField(null=True)
    equipment = ManyToManyField(Equipment, backref="workouts")
    maxhr = IntegerField(null=True)
    minhr = IntegerField(null=True)
    notes = TextField(null=True)
    sources = ManyToManyField(Sources, backref="workouts")
    sport = CharField(default="Unknown")
    starttime = DateTimeTZField(unique=True)
    tags = ManyToManyField(Tags, backref="workouts")
    samples = BinaryJSONField(null=True)
    zone_below_50_lower = IntegerField(null=True)
    zone_below_50_upper = IntegerField(null=True)
    zone_below_50_duration = IntervalField(null=True)
    zone_below_50_percentspentabove = FloatField(null=True)
    zone_50_60_lower = IntegerField(null=True)
    zone_50_60_upper = IntegerField(null=True)
    zone_50_60_duration = IntervalField(null=True)
    zone_50_60_percentspentabove = FloatField(null=True)
    zone_60_70_lower = IntegerField(null=True)
    zone_60_70_upper = IntegerField(null=True)
    zone_60_70_duration = IntervalField(null=True)
    zone_60_70_percentspentabove = FloatField(null=True)
    zone_70_80_lower = IntegerField(null=True)
    zone_70_80_upper = IntegerField(null=True)
    zone_70_80_duration = IntervalField(null=True)
    zone_70_80_percentspentabove = FloatField(null=True)
    zone_80_90_lower = IntegerField(null=True)
    zone_80_90_upper = IntegerField(null=True)
    zone_80_90_duration = IntervalField(null=True)
    zone_80_90_percentspentabove = FloatField(null=True)
    zone_90_100_lower = IntegerField(null=True)
    zone_90_100_upper = IntegerField(null=True)
    zone_90_100_duration = IntervalField(null=True)
    zone_90_100_percentspentabove = FloatField(null=True)

    @cache
    def json_friendly(self):
        j = super().json_friendly()
        j["hrzones"] = defaultdict(dict)
        to_delete = []
        for k, v in j.items():
            if k.startswith("zone_"):
                parts = k.split("_")
                j["hrzones"][f"{parts[1]}_{parts[2]}"][parts[3]] = v
                to_delete.append(k)
        for i in to_delete:
            del j[i]
        return j



class Samples(WorkoutBaseModel):
    samples = BinaryJSONField()
    workout = ForeignKeyField(Workouts)


def get_all_models():
    return [
        HRZones,
        Equipment,
        Tags,
        Sources,
        Sources.tags.get_through_model(),
        Workouts,
        Workouts.sources.get_through_model(),
        Workouts.equipment.get_through_model(),
        Workouts.tags.get_through_model(),
        Samples,
    ]
