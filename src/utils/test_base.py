import unittest
import structlog
import logging
from functools import cache


class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set to_null to False to get logging in all test cases
        cls.logger = TestBase.gen_logger()

    @staticmethod
    @cache
    def gen_logger(to_null=True):
        if to_null:
            structlog.configure_once(
                wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL)
            )
        else:
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
        return structlog.get_logger()
