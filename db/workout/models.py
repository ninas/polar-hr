from peewee import *
from playhouse.postgres_ext import *
from ..enum_field import EnumField, ExtendedEnum
from ..base_model import BaseModel

database = PostgresqlExtDatabase(None)

# types


class EquipmentType(ExtendedEnum):
    WEIGHTS = "weights"
    BANDS = "bands"


class SourceType(ExtendedEnum):
    YOUTUBE = "youtube"
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
    samples = TextField()
    sources = ManyToManyField(Sources, backref="workouts")
    sport = CharField(default="Unknown")
    starttime = DateTimeTZField(unique=True)
    tags = ManyToManyField(Tags, backref="workouts")


class HRZones(WorkoutBaseModel):
    zonetype = EnumField(ZoneType)
    lowerlimit = IntegerField()
    higherlimit = IntegerField()
    duration = IntervalField()
    percentspentabove = FloatField()
    workout = ForeignKeyField(Workouts)
