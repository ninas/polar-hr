import json

from src.api.api import API, TagAPI, QueryAPI
from src.db.workout import models
from src.utils.db_utils import DBConnection
from src.utils import log

WORKOUT_DB = None

LOGGER = log.new_logger()


def get_db():
    global WORKOUT_DB, LOGGER
    if not WORKOUT_DB:
        LOGGER.info("Instantiating new db connection", db_connection="new")
        WORKOUT_DB = DBConnection().workout_db
    else:
        LOGGER.info("Reusing DB connection", db_connection="reuse")
    LOGGER.info("Connection established")
    return WORKOUT_DB


def equipment_http(request):
    """
    /equipment
    """
    return API(request, get_db(), models.Equipment, LOGGER).parse()


def tags_http(request, is_dev=False):
    """
    /tags

    """
    return TagAPI(
        request,
        get_db(),
        [
            models.TagType.TAG,
            models.TagType.SPORT,
            models.TagType.CREATOR,
            models.TagType.EQUIPMENT,
        ],
        LOGGER,
    ).parse()


def exercises_http(request, is_dev=False):
    """
    /exercises

    """
    return TagAPI(request, get_db(), [models.TagType.EXERCISE], LOGGER).parse()


def everything_http(request, is_dev=False):
    """
    /everything

    """
    if request.method != "GET":
        return API.error("Must send as a GET request")
    request.args = {}
    data = {
        "tags": json.loads(tags_http(request))["body"],
        "equipment": json.loads(equipment_http(request))["body"],
        "exercises": json.loads(exercises_http(request))["body"],
        "workouts": json.loads(workouts_http(request))["body"],
        "sources": json.loads(sources_http(request))["body"],
    }

    return API.success(data)


def sources_http(request, is_dev=False):
    return QueryAPI(
        request, get_db(), models.Sources, {"id": int, "url": str,}, LOGGER
    ).parse()


def workouts_http(request, is_dev=False):
    return QueryAPI(
        request, get_db(), models.Workouts, {"id": int, "url": str,}, LOGGER
    ).parse()


if __name__ == "__main__":
    pass
