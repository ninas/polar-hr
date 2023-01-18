# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.paginated_result import PaginatedResult  # noqa: E501
from swagger_server.test import BaseTestCase


class TestExercisesController(BaseTestCase):
    """ExercisesController integration test stubs"""

    def test_all_exercises(self):
        """Test case for all_exercises

        Return all exercises
        """
        response = self.client.open(
            '/ninas2/workout/1.0.0/exercises',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
