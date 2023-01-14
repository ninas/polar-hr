from functools import cache, cached_property

from playhouse.db_url import connect

from src.db.sources import models as source_models
from src.db.workout import models as workout_models
from src.utils import gcp_utils, log, config


class DBConnection:
    UNIX_SOCKET_PATH = "/cloudsql/"

    def __init__(self, logger=None):
        self.logger = logger
        if self.logger is None:
            self.logger = log.new_logger(is_dev=True)

    @cache
    def _connect_to_db(self, model, db_name, host, user, password):
        host = self.UNIX_SOCKET_PATH + host
        self.logger.debug(
            f"Opening connection to DB {db_name}",
            db={"name": db_name, "host": host, "user": user,},
        )
        model.database.init(db_name, host=host, user=user, password=password)
        model.database.connect()
        return model.database

    @cached_property
    def config(self):
        return config.read_config()

    @cached_property
    def source_db(self):
        if "source" not in self.config["db"]:
            raise Exception("No credentials found for sources db")
        return self._connect_to_db(source_models, **self.config["db"]["source"])

    @cached_property
    def workout_db(self):
        if "workout" not in self.config["db"]:
            raise Exception("No credentials found for workouts db")
        return self._connect_to_db(workout_models, **self.config["db"]["workout"])
