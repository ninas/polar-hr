import json
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
    if request.method == "POST" and (
        request.mimetype != "application/json"
        or request.data is None
        or len(request.data) == 0
    ):
        return return_error("Invalid post request")

    results = func(api())
    if len(results) == 0:
        return return_empty()
    return return_success(results)
