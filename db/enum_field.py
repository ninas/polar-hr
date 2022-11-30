from peewee import Field
from enum import Enum


class EnumField(Field):
    def __init__(self, enum, *args, **kwargs):
        if not issubclass(enum, Enum):
            raise TypeError(
                (
                    f"{self.__class__.__name__} Argument enum must be"
                    f" subclass of enum.Enum: {enum} {type(enum)}."
                )
            )
        self.enum = enum
        super().__init__(*args, **kwargs)

    def db_value(self, member):
        return member.value

    def python_value(self, value):
        return self.enum(value)

    def coerce(self, value):
        if value not in self.enum:
            raise ValueError(
                (
                    f"{self.__class__.__name__} the value must be "
                    f"member of the enum: {value}, {self.enum}."
                )
            )

    def pre_field_create(self, model):
        field = "e_%s" % self.name

        tail = ", ".join(["'%s'"] * len(self.enum.list())) % tuple(self.enum.list())
        q = f"CREATE TYPE {field} AS ENUM ({tail});"
        try:
            with self.model._meta.database.atomic():
                self.model._meta.database.execute_sql(q)
        except ProgrammingError as e:
            print(e)

        self.field_type = f"e_{self.name}"

    def post_field_create(self, model):
        self.db_field = f"e_{self.name}"

    def coerce(self, value):
        if value not in self.enum.list():
            raise Exception(f"Invalid Enum Value `{value}`")
        return str(value)

    def delete_type(self):
        try:
            with self.model._meta.database.atomic():
                self.model._meta.database.execute_sql(
                    f"DROP TYPE IF EXISTS e_{self.name};"
                )
        except Exception as e:
            print(f"Failed to drop type {self.field_type}: {e}")

    def get_column_type(self):
        return "enum"

    def __ddl_column__(self, ctype):
        return SQL(f"e_{self.name}")


class ExtendedEnum(str, Enum):
    @classmethod
    def list(cls):
        return [c.value for c in cls]
