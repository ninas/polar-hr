import json
from collections import defaultdict, namedtuple
from functools import cache, cached_property

from src.api.db_base import DBBase
from src.db.workout import models
import swagger_server.models as api_models


@cache
def DBApi():
    return DBBase()


class API:
    def __init__(self, request, model, get_query_params={}):
        self.request = request
        self.model = model
        self.get_query_params = get_query_params

    @staticmethod
    def error(msg=None):
        if msg is None:
            msg = "Invalid request parameters"
        return json.dumps({"statusCode": 400, "message": msg})

    @staticmethod
    def empty_result():
        return json.dumps({"statusCode": 204})

    @staticmethod
    def success(data):
        return json.dumps({"statusCode": 200, "body": data}, indent=4)

    @property
    def methods(self):
        return {"GET": self._get}

    def _result(self, vals, func=None):
        return vals, func if func is not None else API.success

    def parse(self):
        if self.request.method not in self.methods:
            return API.error(
                f"Endpoint does not support {self.request.method} requests. Try: {self.methods}"
            )

        results, res_func = self.methods[self.request.method]()
        if results is None or len(results) == 0:
            return API.empty_result()
        return res_func(results)

    def _flatten_args(self, args):
        data = defaultdict(list)
        for k in args.keys():
            li = args.getlist(k)
            for l in li:
                if len(l) > 0:
                    data[k].extend(l.split(","))
        return data

    def _get(self):
        data = self._flatten_args(self.request.args)

        is_invalid_arg = lambda arg: arg not in data or len(data[arg]) == 0

        if len(data) == 0 or all(
            is_invalid_arg(i) for i in self.get_query_params.keys()
        ):
            return self._result(API.api().get_all(self.model))

        return self._parse_get(data)

    def _parse_get(self, data):
        params = {}
        for name, typ in self.get_query_params.items():
            if name in data:
                params[getattr(self.model, name)] = [typ(i) for i in data[name]]

        return self._result(DBApi().by_id(self.model, params))


class TagAPI(API):
    def __init__(self, request, tag_types):
        super().__init__(request, models.Tags)
        self.tag_types = tag_types

    def _get(self):
        return self._result(
            DBApi().by_id(models.Tags, {models.Tags.tagtype: self.tag_types},)
        )


class QueryAPI(API):
    @property
    def methods(self):
        return {"GET": self._get, "POST": self._post}

    def _post(self):
        if (
            self.request.mimetype != "application/json"
            or self.request.data is None
            or len(self.request.data) == 0
        ):
            return self._result(
                "Invalid post request: make sure you're sending json", API.error
            )
        try:
            q = json.loads(self.request.data)
            if len(q) == 0:
                raise json.decoder.JSONDecodeError()
            data = q
        except json.decoder.JSONDecodeError as e:
            return self._result("Invalid or empty json object passed", API.error)

        return self._parse_post(data)

    def _parse_post(self, data):
        try:
            query = api_models.Query.from_dict(data)
        except Exception as e:
            raise e
            return self._result(None, API.error)

        return self._result(DBApi().query(self.model, query))
