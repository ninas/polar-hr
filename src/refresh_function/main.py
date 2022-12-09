import structlog

from src.utils import gcp_utils, log
from polar import *


def http(request, is_dev=False):
    structlog.contextvars.bind_contextvars(run_reason="refresh")
    log.config_structlog(is_dev)

    logger = structlog.get_logger()
    logger.info("Starting refresh run")
    api = PolarAPI(logger)
    data = api.exercises

    if len(data) > 0:
        logger.debug(
            "Polar API returned workouts",
            workouts=[workout.as_dict_for_logging() for workout in data],
        )

        p = Process(logger)
        workouts = p.map_data(data)

        logger.debug(
            "Workouts to be saved",
            workouts=[workout.as_dict_for_logging() for workout in workouts],
        )

        p.save_to_db(workouts)
    else:
        logger.info("No workouts returned by the API", api_response=api)

    logger.info("Completed run")
    return ""


if __name__ == "__main__":
    http(None, True)
