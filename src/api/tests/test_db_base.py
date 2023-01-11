import unittest
import json
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import src.db.workout.models as models
from src.utils import log
from src.utils.test_base import TestBase
from src.api.db_base import DBBase
import swagger_server.models as api_models


class TestDBBase(TestBase):
    def setUp(self):
        self.db = MagicMock()
        DBBase._get_db = MagicMock(return_value=self.db)
        DBBase._fetch_from_model = MagicMock(side_effect=lambda x: x)

        self.base = DBBase(self.logger, True)

    def test_by_id(self):
        vals = {models.Sources.id: [1, 2], models.Sources.url: ["something"]}

        mod = self.base.by_id(models.Sources, vals)
        comp_mod = models.Sources().select()
        for k, v in vals.items():
            comp_mod = comp_mod.orwhere(k << v)

        self.assertEqual(str(mod), str(comp_mod))

        self.assertRaises(
            Exception, self.base.by_id(models.Sources, {models.Workouts.id: [1]})
        )

    def test_get_all(self):
        self.assertEqual(
            str(models.Sources.select()), self.base.get_all(models.Sources)
        )

    def test_query(self):
        with patch(
            "src.api.db_base.ComplexQuery",
            return_value=MagicMock(execute=MagicMock(side_effect=lambda: {})),
        ) as mock_query:
            self.assertEqual(self.base.query(models.Sources, MagicMock()), {})

            mock_query.return_value.execute.side_effect = lambda: None
            self.assertEqual(self.base.query(models.Sources, MagicMock()), {})
