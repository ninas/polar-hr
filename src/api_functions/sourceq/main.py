import json
from flask import make_response
from datetime import timedelta
from src.api.api_base import APIBase
import swagger_server.models as api_models
from peewee import *

from src.api.api_utils import *
from src.db.workout import models
from src.utils import log
from src.utils.db_utils import DBConnection


def sources_http(request, is_dev=False):
    def func(api, data):
        if request.method == "GET":
            return sources_get(api, data)

        query = api_models.SourceQuery.from_dict(data).query
        if query is None:
            return []

        return api.query_sources(query)

    return base_function(request, func, ["GET", "POST"])


def sources_get(api, data):

    is_invalid_arg = lambda arg: arg not in data or len(data[arg]) == 0
    if len(data) == 0 or (is_invalid_arg("id") and is_invalid_arg("url")):
        return api.fetch_from_model("Sources")

    params = {}
    if not is_invalid_arg("id"):
        params[models.Sources.id] = [int(i) for i in data["id"]]
    if not is_invalid_arg("url"):
        params[models.Sources.url] = data["url"]

    return api.by_id(models.Sources, params)


if __name__ == "__main__":
    pass
