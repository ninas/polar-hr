import json
from datetime import datetime, timedelta
from functools import cache

import isodate
from peewee import Model


class BaseModel(Model):
    def as_dict(self):
        fields = {}
        for field in self._meta.fields.items():
            fields[field[0]] = getattr(self, field[0])
        return fields

    def __str__(self):
        fields = [f"  {name}: {details}" for name, details in self.as_dict().items()]

        fields_str = ";".join(fields)

        return f"{self.__class__.__name__}\n({fields_str})"

    def json_friendly(self):
        fields = self.as_dict()
        for k, v in fields.items():
            if isinstance(v, datetime):
                fields[k] = v.isoformat()
            if isinstance(v, timedelta):
                fields[k] = isodate.duration_isoformat(v)

        return fields
