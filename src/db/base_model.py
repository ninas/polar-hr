from peewee import Model


class BaseModel(Model):
    def __str__(self):
        fields = []
        for field in self._meta.fields.items():
            fields.append(f"\t{field[0]} {field[1]}: {getattr(self, field[0])}")

        fields_str = "\n".join(fields)

        return f"{self.__class__.__name__}\n({fields_str})"
