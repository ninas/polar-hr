import json
from collections import defaultdict, namedtuple
from functools import cache, cached_property

from src.api.db_base import DBBase
from src.db.workout import models
import swagger_server.models as api_models
from src.utils import log


class API:
    def __init__(self, request, model, get_query_params={}, logger=None):
        if logger is None:
            logger = log.new_logger()
        self.logger = logger.bind(
            url=request.base_url, method=request.method, model=model.__class__
        )
        self.request = request
        self.model = model
        self.get_query_params = get_query_params

    @cached_property
    def db_api(self):
        return DBBase(self.logger, False)

    def error(self, msg=None):
        if msg is None:
            msg = "Invalid request parameters"
        self.logger.info("User error", msg=msg, status_code=400)
        return json.dumps({"statusCode": 400, "message": msg})

    def empty_result(self):
        self.logger.info("Empty results", status_code=204)
        return json.dumps({"statusCode": 204})

    def success(self, data):
        self.logger.info("Success", status_code=200)
        return json.dumps({"statusCode": 200, "body": data}, indent=4)

    @property
    def methods(self):
        return {"GET": self._get}

    def _result(self, vals, func=None):
        return vals, func if func is not None else self.success

    def parse(self):
        if self.request.method not in self.methods:
            return self.error(
                f"Endpoint does not support {self.request.method} requests. Try: {self.methods.keys()}"
            )

        results, res_func = self.methods[self.request.method]()

        if results is None or len(results) == 0:
            return self.empty_result()
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
            return self._result(self.db_api.get_all(self.model))

        return self._parse_get(data)

    def _parse_get(self, data):
        params = {}
        for name, typ in self.get_query_params.items():
            if name in data:
                params[getattr(self.model, name)] = [typ(i) for i in data[name]]
        return self._result(self.db_api.by_id(self.model, params))


class TagAPI(API):
    def __init__(self, request, tag_types):
        super().__init__(request, models.Tags)
        self.tag_types = tag_types

    def _get(self):
        return self._result(
            self.db_api.by_id(models.Tags, {models.Tags.tagtype: self.tag_types},)
        )


class QueryAPI(API):
    @property
    def methods(self):
        return {"GET": self._get, "POST": self._post}

    def _validate_api_enum_fields(self, query):
        return [
            self._validate_enum_field(
                query, ("sources_attributes", "source_type"), api_models.SourceType
            ),
            self._validate_enum_field(
                query,
                ("workouts_attributes", "equipment"),
                api_models.EquipmentType,
                "equipment_type",
            ),
            self._validate_enum_field(
                query,
                ("workouts_attributes", "in_hr_zone"),
                api_models.ZoneType,
                "zone_type",
            ),
            self._validate_enum_field(
                query,
                ("workouts_attributes", "above_hr_zone"),
                api_models.ZoneType,
                "zone_type",
            ),
        ]

    def _validate_enum_field(self, query, field_path, model, in_obj=None):
        obj = query
        for i in field_path:
            if getattr(obj, i) is None:
                return None
            obj = getattr(obj, i)
        if len(obj) > 0:
            valid = [
                v
                for k, v in model.__dict__.items()
                if k[0:2] != "__"
                and not callable(v)
                and not isinstance(v, property)
                and not isinstance(v, classmethod)
            ]

            for i in obj:
                if in_obj is not None:
                    i = getattr(i, in_obj)
                if i not in valid:
                    return f"{model.__name__}: Invalid parameter {i}. Valid options are: {valid}"
        return None

    def _post(self):
        if (
            self.request.mimetype != "application/json"
            or self.request.data is None
            or len(self.request.data) == 0
        ):
            return self._result(
                "Invalid post request: make sure you're sending json", self.error
            )
        try:
            data = json.loads(self.request.data)
            if len(data) == 0:
                raise json.decoder.JSONDecodeError()
            self.logger.info("API query", query=data)
        except json.decoder.JSONDecodeError as e:
            return self._result("Invalid or empty json object passed", self.error)

        return self._parse_post(data)

    def _parse_post(self, data):
        query = api_models.Query.from_dict(data)
        # Should prob enable typing to validate all API types
        errs = self._validate_api_enum_fields(query)
        for i in errs:
            if i is not None:
                return self._result(i, self.error)

        return self._result(self.db_api.query(self.model, query))
