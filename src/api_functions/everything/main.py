import json

from src.api.api_base import APIBase
from src.utils import log


def everything_http(request, is_dev=False):
    """
    /everything

    """
    logger = log.new_logger(is_dev=is_dev)
    logger.bind(path="/everything")
    api = APIBase(logger)

    data = {
        "tags": api.tags(),
        "equipment": api.equipment(),
        "workouts": api.workouts(),
        "sources": api.sources(),
    }

    logger.info(f"Total number of tags: {len(data['tags'])}")
    logger.info(f"Total number of equipment entries: {len(data['equipment'])}")
    logger.info(f"Total number of sources: {len(data['sources'])}")
    logger.info(f"Total number of workouts: {len(data['workouts'])}")

    return json.dumps(data)


if __name__ == "__main__":
    print(everything_http(None, True))
