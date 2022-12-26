import json
from collections import defaultdict
from functools import cache

from src.api.api_base import APIBase


def return_error(error="Invalid request parameters"):
    return json.dumps({"statusCode": 400, "body": error})


def return_empty():
    return json.dumps({"statusCode": 204})


def return_success(data):
    return json.dumps({"statusCode": 200, "body": data}, indent=4)


def ensure_get(request):
    if request.method != "GET":
        return return_error("Only GET supported for this endpoint")
    return None


@cache
def api():
    return APIBase()


def base_function(request, func, methods=["GET"]):
    if request.method not in methods:
        return return_error(
            f"Endpoint does not support {request.method} requests. Try: {methods}"
        )

    data = None
    if request.method == "POST":
        if (
            request.mimetype != "application/json"
            or request.data is None
            or len(request.data) == 0
        ):
            return return_error("Invalid post request: make sure you're sending json")
        try:
            q = json.loads(request.data)
            if len(q) == 0:
                raise json.decoder.JSONDecodeError()
            data = q
        except json.decoder.JSONDecodeError as e:
            return return_error("Invalid or empty json object passed")
    elif request.method == "GET" and request.args is not None:
        data = defaultdict(list)
        for k in request.args.keys():
            li = request.args.getlist(k)
            for l in li:
                if len(l) > 0:
                    data[k].extend(l.split(","))

    results = func(api(), data)
    if len(results) == 0:
        return return_empty()
    return return_success(results)
