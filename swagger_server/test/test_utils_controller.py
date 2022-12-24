# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.everything import Everything  # noqa: E501
from swagger_server.test import BaseTestCase


class TestUtilsController(BaseTestCase):
    """UtilsController integration test stubs"""

    def test_everything(self):
        """Test case for everything

        Return all data
        """
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/everything',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_refresh(self):
        """Test case for refresh

        Refresh workout data
        """
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/refresh',
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
