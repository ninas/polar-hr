from src.db.workout import models
from src.utils.db_utils import DBConnection
from src.utils import log
from flask import make_response
import json


def tags_http(request, is_dev=False):
    """
    /tags

    """
    logger = log.new_logger(is_dev=is_dev)
    logger.bind(path="/workouts")
    db = DBConnection(logger).workout_db
    with db.atomic():
        tags = models.Tags.select().execute()

    return_data = [tag.as_dict() for tag in tags]

    return json.dumps(return_data)


if __name__ == "__main__":
    print(tags_http(None, True))
