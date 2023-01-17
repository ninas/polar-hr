import logging
import unittest
from functools import cache

import structlog
import testing.postgresql
from src.utils.test_db import PG_DB
from src.db.workout import models


def tearDownModule():
    PG_DB.clear_cache()


class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set to_null to False to get logging in all test cases
        cls.logger = TestBase.gen_logger()

    @classmethod
    def create_test_db(cls, insert_data=True):
        if insert_data:
            cls.pg_db = PG_DB()
        else:
            cls.pg_db = testing.postgresql.Postgresql()
        db = models.database
        db.init(**cls.pg_db.dsn())
        db.connect()
        if not insert_data:
            db.create_tables(models.get_all_models())
        return db

    @classmethod
    def teardown_test_db(cls):
        if cls.pg_db is not None:
            cls.pg_db.stop()

    @staticmethod
    @cache
    def gen_logger(to_null=True):
        if to_null:
            structlog.configure_once(
                wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL)
            )
        else:
            logger = logging.getLogger("peewee")
            logger.addHandler(logging.StreamHandler())
            logger.setLevel(logging.DEBUG)

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


class TestConsts:
    YOUTUBE_ID = "dQw4w9WgXcQ"
    YOUTUBE_URLS = [
        f"https://youtube.com/shorts/{YOUTUBE_ID}?feature=share",
        f"//www.youtube-nocookie.com/embed/{YOUTUBE_ID}?rel=0",
        f"http://www.youtube.com/user/Scobleizer#p/u/1/{YOUTUBE_ID}",
        f"https://www.youtube.com/watch?v={YOUTUBE_ID}&feature=channel",
        f"http://www.youtube.com/watch?v={YOUTUBE_ID}&playnext_from=TL&videos=osPknwzXEas&feature=sub",
        f"http://www.youtube.com/ytscreeningroom?v={YOUTUBE_ID}",
        f"http://www.youtube.com/user/SilkRoadTheatre#p/a/u/2/{YOUTUBE_ID}",
        f"http://youtu.be/{YOUTUBE_ID}",
        f"http://www.youtube.com/watch?v={YOUTUBE_ID}&feature=youtu.be",
        f"http://youtu.be/{YOUTUBE_ID}",
        f"https://www.youtube.com/user/Scobleizer#p/u/1/{YOUTUBE_ID}?rel=0",
        f"http://www.youtube.com/watch?v={YOUTUBE_ID}&feature=channel",
        f"http://www.youtube.com/watch?v={YOUTUBE_ID}&playnext_from=TL&videos=osPknwzXEas&feature=sub",
        f"http://www.youtube.com/ytscreeningroom?v={YOUTUBE_ID}",
        f"http://www.youtube.com/embed/{YOUTUBE_ID}?rel=0",
        f"http://www.youtube.com/watch?v={YOUTUBE_ID}",
        f"http://youtube.com/v/{YOUTUBE_ID}?feature=youtube_gdata_player",
        f"http://youtube.com/vi/{YOUTUBE_ID}?feature=youtube_gdata_player",
        f"http://youtube.com/?v={YOUTUBE_ID}&feature=youtube_gdata_player",
        f"http://www.youtube.com/watch?v={YOUTUBE_ID}&feature=youtube_gdata_player",
        f"http://youtube.com/?vi={YOUTUBE_ID}&feature=youtube_gdata_player",
        f"http://youtube.com/watch?v={YOUTUBE_ID}&feature=youtube_gdata_player",
        f"http://youtube.com/watch?vi={YOUTUBE_ID}&feature=youtube_gdata_player",
        f"http://youtu.be/{YOUTUBE_ID}?feature=youtube_gdata_player",
        f"www.youtu.be/{YOUTUBE_ID}",
    ]
