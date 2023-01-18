import unittest
import json
from datetime import timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, patch, ANY

import src.db.workout.models as models
from src.utils import log
from src.utils.test_base import TestBase
from src.workout_sources.video_source import VideoSource
from src.api.api import API, QueryAPI
import swagger_server.models as api_models


class TestAPI(TestBase):
    def setUp(self):
        self.request = MagicMock(method="GET")
        self.request.args = MagicMock(
            keys=MagicMock(return_value=["a"]),
            getlist=MagicMock(return_value=["aa", "bb"]),
        )
        self.model = MagicMock(a=MagicMock(), __name__="Tags")
        self.db = MagicMock()
        self.api = API(self.db, self.logger)
        self.api.db_api = MagicMock(get_all=MagicMock(), by_id=MagicMock())

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
            vals = self.api.parse(self.request, self.model, {"a": int})
            loaded = json.loads(vals)
            self.assertEqual(loaded["statusCode"], 400)

        self.api._get = MagicMock(return_value=self.api._result([]))
        vals = self.api.parse(self.request, self.model)
        loaded = json.loads(vals)
        self.assertEqual(loaded["statusCode"], 204)

        self.api._get.return_value = self.api._result(
            {"data": ["aa", "bb"], "nextPage": -1}
        )
        vals = self.api.parse(self.request, self.model)
        self.api._get.assert_called()

    def test_pagination_parsing(self):
        self.api._parse_get = MagicMock(
            return_value=self.api._result({"data": ["something"], "nextPage": 2})
        )

        self.request.args = MagicMock(
            keys=MagicMock(return_value=["id"]), getlist=MagicMock(side_effect=[["1"]]),
        )
        self.api.parse(self.request, self.model, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, None)

        self.request.args.keys.return_value.append("paginate")
        self.request.args.getlist.side_effect = [["1"], ["true"]]
        self.api.parse(self.request, self.model, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 1)

        self.request.args.getlist.side_effect = [["1"], ["false"]]
        self.api.parse(self.request, self.model, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, None)
        self.request.args.getlist.side_effect = [["1"], ["aaa"]]
        self.api.parse(self.request, self.model, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, None)
        self.request.args.getlist.side_effect = [["1"], ["false,true,true", "true"]]
        self.api.parse(self.request, self.model, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, None)

        self.request.args.keys.return_value = ["id", "paginationId"]
        self.request.args.getlist.side_effect = [["1"], ["2"]]
        self.api.parse(self.request, self.model, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 2)

        self.request.args.getlist.side_effect = [["1"], ["a"]]
        res = json.loads(self.api.parse(self.request, self.model, {"id": str}))
        self.assertEqual(res["statusCode"], 400)
        self.request.args.getlist.side_effect = [["1"], ["0"]]
        res = json.loads(self.api.parse(self.request, self.model, {"id": str}))
        self.assertEqual(res["statusCode"], 400)

        self.request.args.keys.return_value = ["id", "paginate", "paginationId"]
        self.request.args.getlist.side_effect = [["1"], ["false"], ["2"]]
        self.api.parse(self.request, self.model, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 2)

    def test_pagination_by_default(self):
        self.api._parse_get = MagicMock(
            return_value=self.api._result({"data": ["something"], "nextPage": 2})
        )

        self.request.args = MagicMock(
            keys=MagicMock(return_value=["id"]), getlist=MagicMock(side_effect=[["1"]]),
        )
        self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 1)

        self.request.args.keys.return_value.append("paginate")
        self.request.args.getlist.side_effect = [["1"], ["true"]]
        self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 1)

        self.request.args.getlist.side_effect = [["1"], ["false"]]
        self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 1)
        self.request.args.getlist.side_effect = [["1"], ["aaa"]]
        self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 1)
        self.request.args.getlist.side_effect = [["1"], ["false,true,true", "true"]]
        self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 1)

        self.request.args.keys.return_value = ["id", "paginationId"]
        self.request.args.getlist.side_effect = [["1"], ["2"]]
        self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 2)

        self.request.args.getlist.side_effect = [["1"], ["a"]]
        res = json.loads(
            self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        )
        self.assertEqual(res["statusCode"], 400)
        self.request.args.getlist.side_effect = [["1"], ["0"]]
        res = json.loads(
            self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        )
        self.assertEqual(res["statusCode"], 400)

        self.request.args.keys.return_value = ["id", "paginate", "paginationId"]
        self.request.args.getlist.side_effect = [["1"], ["false"], ["2"]]
        self.api.parse(self.request, models.SourcesMaterialized, {"id": str})
        self.api._parse_get.assert_called_with(ANY, ANY, ANY, 2)

    def test_parse_get(self):
        self.api.parse(self.request, self.model, {"a": str})
        self.api.db_api.by_id.assert_called_with(
            self.model, {self.model.a: ["aa", "bb"]}, None
        )

        self.api.get_query_params = {"c": str}
        self.api.parse(self.request, self.model)
        self.api.db_api.get_all.assert_called()


class TestQueryAPI(TestBase):
    def setUp(self):
        self.db = MagicMock()
        self.model = MagicMock()
        self.mock_db_return = MagicMock(
            get_all=MagicMock(), by_id=MagicMock(), query=MagicMock()
        )

    def _run(
        self,
        status_code,
        request_data=None,
        query={"workoutsAttributes": {"sport": ["sport1"]}},
        pagination_id=None,
        has_request_data=True,
    ):
        request = MagicMock(method="POST", mimetype="application/json")

        if request_data is None:
            request_data = json.dumps(query, indent=1)
        if has_request_data:
            request.data = request_data

        api = QueryAPI(self.db, logger=self.logger)
        api.db_api = self.mock_db_return
        vals = api.parse(request, self.model)

        loaded = json.loads(vals)

        self.assertEqual(loaded["statusCode"], status_code)
        if status_code != 400:
            api.db_api.query.assert_called_with(
                self.model, api_models.Query.from_dict(query), pagination_id
            )

    def test_pagination_post(self):
        self.mock_db_return.query.return_value = {
            "data": {"something": "yup"},
            "nextPage": -1,
        }
        self._run(
            200,
            query={"paginate": True, "workoutsAttributes": {"sport": ["sport1"]}},
            pagination_id=1,
        )
        self._run(
            200,
            query={"paginate": False, "workoutsAttributes": {"sport": ["sport1"]}},
            pagination_id=None,
        )
        self._run(
            200,
            query={"paginationId": 2, "workoutsAttributes": {"sport": ["sport1"]}},
            pagination_id=2,
        )
        self._run(
            200,
            query={
                "paginate": False,
                "paginationId": 2,
                "workoutsAttributes": {"sport": ["sport1"]},
            },
            pagination_id=2,
        )

    def test_parse_post(self):
        # didn't define a return so this should give us a 204
        self._run(204)

        self.mock_db_return.query.return_value = {
            "data": {"something": "yup"},
            "nextPage": -1,
        }
        self._run(200)

        self._run(400, has_request_data=False)

        # This will raise a json.decoder.JSONDecodeError
        self._run(400, "")

    def test_enum_typing(self):
        query = {"workoutsAttributes": {"equipment": [{"equipmentType": "weights"}]}}
        self.mock_db_return.query.return_value = {
            "data": {"something": "yup"},
            "nextPage": -1,
        }
        self._run(200, query=query)

        query = {"workoutsAttributes": {"equipment": [{"equipmentType": "invalid"}]}}
        self._run(400, query=query)

        # Test when not nested in outer obj
        query = {"sourcesAttributes": {"sourceType": ["youtube", "invalid"]}}
        self.mock_db_return.query.return_value = {"something": "yup"}
        self._run(400, query=query)
