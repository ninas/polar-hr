# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.workout import Workout  # noqa: E501
from swagger_server.models.workout_query import WorkoutQuery  # noqa: E501
from swagger_server.test import BaseTestCase


class TestWorkoutController(BaseTestCase):
    """WorkoutController integration test stubs"""

    def test_get_workouts(self):
        """Test case for get_workouts

        Retrieve a specific workout or all if no ids are specified
        """
        query_string = [('id', 56),
                        ('samples', true)]
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/workouts',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_search_for_workouts(self):
        """Test case for search_for_workouts

        Search for workouts
        """
        body = WorkoutQuery()
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/workouts',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
