import json
from polar import *

from src.utils import gcp_utils, log


def http(request, is_dev=False):
    logger = log.new_logger("refresh", is_dev)
    logger.info("Starting refresh run")
    api = PolarAPI(logger)
    data = api.exercises

    if len(data) > 0:
        logger.debug(
            "Polar API returned workouts",
            workouts=[workout.as_dict_for_logging() for workout in data],
        )

        p = ProcessData(logger)
        workouts = p.map_data(data)

        logger.debug(
            "Workouts to be saved",
            workouts=[workout.as_dict_for_logging() for workout in workouts],
        )

        p.save_to_db(workouts)
    else:
        logger.info("No workouts returned by the API", api_response=api)

    logger.info("Completed run")

    response = {"statusCode": 200, "body": ""}
    return json.dumps(response, indent=4)


if __name__ == "__main__":
    http(None, True)
