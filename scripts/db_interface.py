from overrides import EnforceOverrides
from db import models


class DBInterface(EnforceOverrides):
    def __init__(self, db, data):
        self.db = db
        self._data = data
        self.model = None

    @property
    def data(self):
        return self._data

    def insert_row(self):
        pass

    @staticmethod
    def _find(db, model, field, val):
        try:
            with db.atomic():
                return model.get(field == val)
        except model.DoesNotExist:
            pass
        return None

    def _val_or_none(self, keys, typ=None, data=None):
        if data is None:
            data = self.data
        d = data
        for i in keys:
            if isinstance(i, int) and (isinstance(d, list) or isinstance(d, tuple)):
                if len(d) < i:
                    return None
                d = d[i]
            elif isinstance(d, dict) and i in d:
                d = d[i]
            else:
                return None
        return typ(d) if typ is not None else d

    def _insert_tags(self, data, type_data):
        insert_data = [{
            "name": val,
            "tagtype": type_data
        } for val in data]
        with self.db.atomic():
            inserts = models.Tags.insert_many(insert_data).on_conflict_ignore().execute()

            all_models = models.Tags.select().where(models.Tags.name << data).execute()
        if inserts is not None and len(inserts) > 0:
            new_inserts = set(i[0] for i in inserts)
            for i in all_models:
                if i.id in new_inserts:
                    print("New:", i.name)
        return all_models
