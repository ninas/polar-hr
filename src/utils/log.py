import logging
from functools import cache

import google.cloud.logging
import structlog
from google.cloud.logging_v2.handlers import StructuredLogHandler, setup_logging

from src.utils import gcp_utils


@cache
def enable_debug_logging():
    # For the moment, since this is used in a cloud function, don't allow changing this during runtime
    debug = gcp_utils.fetch_config("refresh_func/debug_logging") == "1"
    if debug:
        print("debug logging enabled")

    return debug


@cache
def log_level():
    return logging.DEBUG if enable_debug_logging() else logging.INFO


def set_default_log_level():
    logger = logging.getLogger()
    logger.setLevel(log_level())


# Cheating and using this to ensure it is only run once
@cache
def init_cloud_logging():
    client = google.cloud.logging.Client()
    handler = StructuredLogHandler()
    setup_logging(handler)
    set_default_log_level()


@cache
def config_structlog(is_dev=False):
    def googlify(logger, method_name, event_dict):
        if "severity" not in event_dict:
            event_dict["severity"] = event_dict["level"].upper()
            del event_dict["level"]
        if "message" not in event_dict:
            event_dict["message"] = event_dict["event"]
            del event_dict["event"]
        return event_dict

    if is_dev:
        structlog.configure_once(
            processors=[
                structlog.processors.CallsiteParameterAdder(
                    [
                        structlog.processors.CallsiteParameter.PATHNAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ],
                ),
                structlog.dev.set_exc_info,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )
    else:
        init_cloud_logging()
        structlog.configure_once(
            wrapper_class=structlog.make_filtering_bound_logger(log_level()),
            processors=[
                structlog.processors.dict_tracebacks,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.add_log_level,
                structlog.processors.CallsiteParameterAdder(
                    [
                        structlog.processors.CallsiteParameter.PATHNAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ],
                ),
                googlify,
                structlog.processors.JSONRenderer(),
            ],
        )


def new_logger(name=None, is_dev=False):
    if name is not None:
        structlog.contextvars.bind_contextvars(run_reason=name)
    config_structlog(is_dev)
    return structlog.get_logger()
