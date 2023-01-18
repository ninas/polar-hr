import json

from src.api.api import API, TagAPI, QueryAPI
from src.db.workout import models
from src.utils.db_utils import DBConnection
from src.utils import log

WORKOUT_DB = None

LOGGER = log.new_logger()

STORED_APIS = {"API": None, "TagAPI": None, "QueryAPI": None}


def get_db():
    global WORKOUT_DB, LOGGER
    if not WORKOUT_DB:
        LOGGER.info("Instantiating new db connection", db_connection="new")
        WORKOUT_DB = DBConnection(LOGGER).workout_db
    else:
        LOGGER.info("Reusing DB connection", db_connection="reuse")
    LOGGER.info("Connection established")
    return WORKOUT_DB


def get_api(api_type=API):
    name = api_type.__name__
    if name in STORED_APIS and STORED_APIS[name] is not None:
        return STORED_APIS[name]
    STORED_APIS[name] = api_type(get_db(), LOGGER)
    return STORED_APIS[name]


def equipment_http(request):
    """
    /equipment
    """
    return get_api().parse(request, models.Equipment)


def tags_http(request, is_dev=False):
    """
    /tags

    """
    return TagAPI(
        get_db(),
        [
            models.TagType.TAG,
            models.TagType.SPORT,
            models.TagType.CREATOR,
            models.TagType.EQUIPMENT,
        ],
        LOGGER,
    ).parse(request, models.Tags)


def exercises_http(request, is_dev=False):
    """
    /exercises

    """
    return TagAPI(get_db(), [models.TagType.EXERCISE], LOGGER).parse(
        request, models.Tags
    )


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
    return get_api(QueryAPI).parse(
        request, models.SourcesMaterialized, {"id": int, "url": str,}
    )


def workouts_http(request, is_dev=False):
    return get_api(QueryAPI).parse(
        request, models.WorkoutsMaterialized, {"id": int, "url": str,}
    )


if __name__ == "__main__":
    pass
