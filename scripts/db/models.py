from peewee import *
from playhouse.postgres_ext import *
from db.enum_field import EnumField, ExtendedEnum

database = PostgresqlExtDatabase(None)

# types


class EquipmentType(ExtendedEnum):
    WEIGHTS = "Weights"
    BANDS = "Bands"


class SourceType(ExtendedEnum):
    YOUTUBE = "Youtube"
    UNKNOWN = "Unknown"


class ZoneType(ExtendedEnum):
    BELOW_50 = "BELOW_FIFTY"
    FIFTY_60 = "FIFTY_60"
    SIXTY_70 = "SIXTY_70"
    SEVENTY_80 = "SEVENTY_80"
    EIGHTY_90 = "EIGHTY_90"
    NINETY_100 = "NINETY_100"


# tables


class BaseModel(Model):
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

    """
    def __str__(self):
        return
        to_print = []
        for i in dir(self):
            if not callable(i) and (i[:2] != "__" and i[-2:] != "__"):
                to_print.append(f"{getattr(self, i)}")
        return f"{self.__name__}({', '.join(to_print)})"
    """


class Exercises(BaseModel):
    name = TextField(unique=True)


class Tags(BaseModel):
    name = TextField(unique=True)


class Equipment(BaseModel):
    equipmenttype = EnumField(EquipmentType)
    magnitude = TextField()
    quantity = IntegerField(constraints=[SQL("DEFAULT 1")], null=True)


class Sources(BaseModel):
    extrainfo = JSONField(null=True)
    length = IntervalField(null=True)
    creator = TextField(null=True)
    name = TextField(null=True)
    sourcetype = EnumField(SourceType)
    url = TextField(unique=True)
    exercises = ManyToManyField(Exercises, backref="sources")
    tags = ManyToManyField(Tags, backref="sources")


class Workouts(BaseModel):
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


class HRZones(BaseModel):
    zonetype = EnumField(ZoneType)
    lowerlimit = IntegerField()
    higherlimit = IntegerField()
    duration = IntervalField()
    percentspentabove = FloatField()
    workout = ForeignKeyField(Workouts)
