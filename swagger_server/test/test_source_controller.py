# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.query import Query  # noqa: E501
from swagger_server.models.source import Source  # noqa: E501
from swagger_server.test import BaseTestCase


class TestSourceController(BaseTestCase):
    """SourceController integration test stubs"""

    def test_get_sources(self):
        """Test case for get_sources

        Retrieve a specific source using its id or all if no ids are specified
        """
        query_string = [('id', 56),
                        ('url', 56)]
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/sources',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_search_for_sources(self):
        """Test case for search_for_sources

        Search for sources
        """
        body = Query()
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/sources',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
