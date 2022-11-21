import unittest

from utils import *


class TestUtils(unittest.TestCase):
    TEST_VID_ID = "dQw4w9WgXcQ"
    TEST_URLS = [
        f"https://youtube.com/shorts/{TEST_VID_ID}?feature=share",
        f"//www.youtube-nocookie.com/embed/{TEST_VID_ID}?rel=0",
        f"http://www.youtube.com/user/Scobleizer#p/u/1/{TEST_VID_ID}",
        f"https://www.youtube.com/watch?v={TEST_VID_ID}&feature=channel",
        f"http://www.youtube.com/watch?v={TEST_VID_ID}&playnext_from=TL&videos=osPknwzXEas&feature=sub",
        f"http://www.youtube.com/ytscreeningroom?v={TEST_VID_ID}",
        f"http://www.youtube.com/user/SilkRoadTheatre#p/a/u/2/{TEST_VID_ID}",
        f"http://youtu.be/{TEST_VID_ID}",
        f"http://www.youtube.com/watch?v={TEST_VID_ID}&feature=youtu.be",
        f"http://youtu.be/{TEST_VID_ID}",
        f"https://www.youtube.com/user/Scobleizer#p/u/1/{TEST_VID_ID}?rel=0",
        f"http://www.youtube.com/watch?v={TEST_VID_ID}&feature=channel",
        f"http://www.youtube.com/watch?v={TEST_VID_ID}&playnext_from=TL&videos=osPknwzXEas&feature=sub",
        f"http://www.youtube.com/ytscreeningroom?v={TEST_VID_ID}",
        f"http://www.youtube.com/embed/{TEST_VID_ID}?rel=0",
        f"http://www.youtube.com/watch?v={TEST_VID_ID}",
        f"http://youtube.com/v/{TEST_VID_ID}?feature=youtube_gdata_player",
        f"http://youtube.com/vi/{TEST_VID_ID}?feature=youtube_gdata_player",
        f"http://youtube.com/?v={TEST_VID_ID}&feature=youtube_gdata_player",
        f"http://www.youtube.com/watch?v={TEST_VID_ID}&feature=youtube_gdata_player",
        f"http://youtube.com/?vi={TEST_VID_ID}&feature=youtube_gdata_player",
        f"http://youtube.com/watch?v={TEST_VID_ID}&feature=youtube_gdata_player",
        f"http://youtube.com/watch?vi={TEST_VID_ID}&feature=youtube_gdata_player",
        f"http://youtu.be/{TEST_VID_ID}?feature=youtube_gdata_player",
        f"www.youtu.be/{TEST_VID_ID}",
    ]

    def test_vid_id(self):
        for u in self.TEST_URLS:
            self.assertEqual(youtube_vid_id(u), "dQw4w9WgXcQ")
