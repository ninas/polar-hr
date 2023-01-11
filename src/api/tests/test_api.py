import unittest
import json
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import src.db.workout.models as models
from src.utils import log
from src.utils.test_base import TestBase
from src.workout_sources.video_source import VideoSource
from src.api.api import API, DBApi, QueryAPI
import swagger_server.models as api_models


class TestAPI(TestBase):
    def setUp(self):
        self.request = MagicMock(method="GET")
        self.request.args = MagicMock(
            keys=MagicMock(return_value=["a"]),
            getlist=MagicMock(return_value=["aa", "bb"]),
        )
        self.model = MagicMock(a=MagicMock())
        self.api = API(self.request, self.model, {"a": str}, self.logger)

    def test_flatten_args(self):
        args = self.request.args
        self.assertEqual(self.api._flatten_args(args), {"a": ["aa", "bb"]})

        args.getlist.return_value = ["aa,bb"]
        self.assertEqual(self.api._flatten_args(args), {"a": ["aa", "bb"]})

        args.keys.return_value = ["a", "b"]
        res = [["aa,bb", "cc"], ["dd", "ee"]]
        args.getlist = MagicMock(side_effect=res)
        self.assertEqual(
            self.api._flatten_args(args), {"a": ["aa", "bb", "cc"], "b": ["dd", "ee"]}
        )

    def test_parse_basics(self):
        with patch(
            __name__ + ".API.methods", new_callable=PropertyMock,
        ) as mock_methods:
            mock_methods.return_value = {"something": None}
            vals = self.api.parse()
            loaded = json.loads(vals)
            self.assertEqual(loaded["statusCode"], 400)

        self.api._get = MagicMock(return_value=self.api._result([]))
        vals = self.api.parse()
        loaded = json.loads(vals)
        self.assertEqual(loaded["statusCode"], 204)

        self.api._get.return_value = self.api._result(["aa", "bb"])
        vals = self.api.parse()
        self.api._get.assert_called()

    @patch(
        "src.api.api.DBApi",
        return_value=MagicMock(get_all=MagicMock(), by_id=MagicMock()),
    )
    def test_parse_get(self, db_api_mock):
        self.api.parse()
        db_api_mock().by_id.assert_called_with(self.model, {self.model.a: ["aa", "bb"]})

        self.api.get_query_params = {"c": str}
        self.api.parse()
        db_api_mock().get_all.assert_called()


class TestQueryAPI(TestBase):
    def setUp(self):
        self.model = MagicMock()
        self.mock_db_return = MagicMock(
            get_all=MagicMock(), by_id=MagicMock(), query=MagicMock()
        )

    def _run(
        self,
        status_code,
        request_data=None,
        query={"workoutsAttributes": {"sport": ["sport1"]}},
        has_request_data=True,
    ):
        request = MagicMock(method="POST", mimetype="application/json")

        if request_data is None:
            request_data = json.dumps(query, indent=1)
        if has_request_data:
            request.data = request_data

        with patch("src.api.api.DBApi", return_value=self.mock_db_return) as db:
            api = QueryAPI(request, self.model, logger=self.logger)
            vals = api.parse()

            loaded = json.loads(vals)

            self.assertEqual(loaded["statusCode"], status_code)
            if status_code != 400:
                db().query.assert_called_with(
                    self.model, api_models.Query.from_dict(query)
                )

    def test_parse_post(self):
        # didn't define a return so this should give us a 204
        self._run(204)

        self.mock_db_return.query.return_value = {"something": "yup"}
        self._run(200)

        self._run(400, has_request_data=False)

        # This will raise a json.decoder.JSONDecodeError
        self._run(400, "")

    def test_enum_typing(self):
        query = {"workoutsAttributes": {"equipment": [{"equipmentType": "weights"}]}}
        self.mock_db_return.query.return_value = {"something": "yup"}
        self._run(200, query=query)

        query = {"workoutsAttributes": {"equipment": [{"equipmentType": "invalid"}]}}
        self.mock_db_return.query.return_value = {"something": "yup"}
        self._run(400, query=query)

        # Test when not nested in outer obj
        query = {"sourcesAttributes": {"sourceType": ["youtube", "invalid"]}}
        self.mock_db_return.query.return_value = {"something": "yup"}
        self._run(400, query=query)
