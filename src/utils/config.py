from functools import cache
import json


@cache
def read_config(path="app_config.json"):
    with open(path) as f:
        return json.loads(f.read())
