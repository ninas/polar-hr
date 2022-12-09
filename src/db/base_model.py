import json
from datetime import datetime
from functools import cache
from peewee import Model


class BaseModel(Model):
    def as_dict(self):
        fields = {}
        for field in self._meta.fields.items():
            fields[field[0]] = {
                "type": str(field[1]),
                "value": getattr(self, field[0])
            }
        return fields


    def __str__(self):
        fields = [f"\t{name} {details['type']}: {details['value']}"
                  for name, details in self.as_dict().items()]

        fields_str = "\n".join(fields)

        return f"{self.__class__.__name__}\n({fields_str})"

    def as_json(self):
        vals  = self.as_dict()
        for k,v in vals.items():
            if isinstance(v, datetime):
                vals[k] = str(v)
        return json.dumps(vals)
