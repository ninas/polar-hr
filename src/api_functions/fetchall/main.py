import json

from src.api.api_base import APIBase
from src.api.api_utils import *
from src.db.workout import models
from src.utils import log


def equipment_http(request):
    """
    /equipment
    """
    func = lambda api: api.fetch_from_model("Equipment")
    return base_function(request, func)


def tags_http(request, is_dev=False):
    """
    /tags

    """

    def func(api):
        return api.by_id(
            models.Tags,
            {
                models.Tags.tagtype: [
                    models.TagType.TAG,
                    models.TagType.SPORT,
                    models.TagType.CREATOR,
                    models.TagType.EQUIPMENT,
                ]
            },
        )

    return base_function(request, func)


def exercises_http(request, is_dev=False):
    """
    /exercises

    """
    func = lambda api: api.by_id(
        models.Tags, {models.Tags.tagtype: [models.TagType.EXERCISE]}
    )
    return base_function(request, func)


def everything_http(request, is_dev=False):
    """
    /everything

    """
    func = lambda api: {
        "tags": tags_http(request),
        "equipment": equipment_http(request),
        "exercises": exercises_http(request),
        "workouts": api.fetch_from_model("Workouts"),
        "sources": api.fetch_from_model("Sources"),
    }

    return base_function(request, func)


if __name__ == "__main__":
    pass
