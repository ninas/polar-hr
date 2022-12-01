import unittest

from db_interface import DBInterface


class TestDBInterface(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            "one": "1",
            "two": ["three", "four", {"five": {"six": "6"}}],
            "seven": {"eight": {"nine": 9}},
        }

        self.intf = DBInterface(None, self.test_data)

    def test_val_or_none(self):
        self.assertEqual(self.intf._val_or_none(["one"], int), 1)
        self.assertEqual(self.intf._val_or_none(["one"]), "1")
        self.assertEqual(self.intf._val_or_none(["two", 0]), "three")
        self.assertEqual(self.intf._val_or_none(["two", 2, "five", "six"], int), 6)
        self.assertEqual(self.intf._val_or_none(["two", 4, "something"], int), None)
        self.assertEqual(self.intf._val_or_none(["two", "something"], int), None)
        self.assertEqual(self.intf._val_or_none(["seven", 0], int), None)
