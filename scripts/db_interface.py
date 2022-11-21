from overrides import EnforceOverrides


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
