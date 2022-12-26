import json

from src.api.api import API, TagAPI, QueryAPI
from src.db.workout import models
from src.utils import log


def equipment_http(request):
    """
    /equipment
    """
    return API(request, models.Equipment).parse()


def tags_http(request, is_dev=False):
    """
    /tags

    """
    return TagAPI(
        request,
        [
            models.TagType.TAG,
            models.TagType.SPORT,
            models.TagType.CREATOR,
            models.TagType.EQUIPMENT,
        ],
    ).parse()


def exercises_http(request, is_dev=False):
    """
    /exercises

    """
    return TagAPI(request, [models.TagType.EXERCISE]).parse()


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
    return QueryAPI(request, models.Sources, {"id": int, "url": str,}).parse()


def workouts_http(request, is_dev=False):
    return QueryAPI(request, models.Workouts, {"id": int, "url": str,}).parse()


if __name__ == "__main__":
    pass
