from playhouse.db_url import connect
from functools import cache, cached_property

from src.utils import gcp_utils
from src.db.sources import models as source_models
from src.db.workout import models as workout_models


class DBConnection:
    UNIX_SOCKET_PATH = "/cloudsql/"

    def __init__(self, logger):
        self.logger = logger

    @cache
    def _database_connection_data(self, prefix):
        return (
            [gcp_utils.fetch_config(f"{prefix}/db_name")],
            {
                "host": self.UNIX_SOCKET_PATH
                + gcp_utils.fetch_config(f"{prefix}/gcp_path"),
                "user": gcp_utils.fetch_config(f"{prefix}/username"),
                "password": gcp_utils.get_secret("db_workout"),
            },
        )

    @cache
    def _connect_to_db(self, name, model):
        db_name, connection_info = self._database_connection_data(name)
        self.logger.debug(
            f"Opening connection to DB {name}",
            db={
                "name": db_name[0],
                "host": connection_info["host"],
                "user": connection_info["user"],
            },
        )
        model.database.init(db_name[0], **connection_info)
        model.database.connect()
        return model.database

    @cached_property
    def source_db(self):
        return self._connect_to_db("sources_db", source_models)

    @cached_property
    def workout_db(self):
        return self._connect_to_db("workout_db", workout_models)
