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


def sources_query_http(request, is_dev=False):
    def func(api):
        if request.method == "GET":
            return api.sources()

        q = json.loads(request.data)
        if len(q) == 0:
            return return_empty()

        query = api_models.SourceQuery.from_dict(q).query
        if query is None:
            return return_empty()

        return api.query_sources(query)

    return base_function(request, func, ["GET", "POST"])


if __name__ == "__main__":
    pass
