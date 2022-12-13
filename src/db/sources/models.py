from peewee import *
from playhouse.postgres_ext import *

from ..base_model import BaseModel

database = PostgresqlExtDatabase(None)


class SourceInput(BaseModel):
    class Meta:
        database = database

    sources = TextField()
    weights = TextField(null=True)
    bands = TextField(null=True)
    created = DateTimeTZField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    notes = TextField(null=True)
