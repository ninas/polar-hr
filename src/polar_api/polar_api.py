import json
from functools import cache, cached_property

import structlog
from requests_oauthlib import OAuth2Session

from src.polar_api.polar_data_store import PolarDataStore
from src.utils import gcp_utils


class PolarAPI:
    POLAR_EXERCISE_URL = (
        "https://www.polaraccesslink.com/v3/exercises?samples=true&zones=true"
    )

    def __init__(self, logger=None, use_cache=False, write_cache=False):
        self.use_cache = use_cache
        self.write_cache = write_cache
        if logger is None:
            logger = structlog.get_logger()
        self.logger = logger
        self.logger.debug(f"Using cache: {self.use_cache}")

    @cache
    def _get_secret(self, name):
        return gcp_utils.get_secret(name)

    @cached_property
    def session(self):
        return OAuth2Session(
            self._get_secret("polar_client_id"),
            token={"access_token": self._get_secret("polar_token")},
        )

    @property
    def exercises(self):
        if not self.use_cache:
            workouts = self.session.get(self.POLAR_EXERCISE_URL)
            if workouts.status_code != 200:
                self.logger.error(
                    "Error retrieving workouts",
                    extra={"request": workouts, "status_code": workouts.status_code},
                )
                return []
            data = workouts.json()

            if self.write_cache:
                with open("cache", "w") as f:
                    f.write(json.dumps(data, indent=4))
        else:
            with open("cache") as f:
                data = json.loads(f.read())

        exer = [PolarDataStore(i) for i in data]
        return sorted(exer, key=lambda x: x.start_time)
