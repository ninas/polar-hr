# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.source import Source  # noqa: E501
from swagger_server.models.source_query import SourceQuery  # noqa: E501
from swagger_server.test import BaseTestCase


class TestSourceController(BaseTestCase):
    """SourceController integration test stubs"""

    def test_all_sources(self):
        """Test case for all_sources

        Return all sources
        """
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/sources',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_source_by_id(self):
        """Test case for get_source_by_id

        Retrieve a specific source using its id
        """
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/source/{sourceId}'.format(sourceId=789),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_source_by_url(self):
        """Test case for get_source_by_url

        Retrieve a specific source using its url
        """
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/source/url/{sourceUrl}'.format(sourceUrl='sourceUrl_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_search_for_sources(self):
        """Test case for search_for_sources

        Search for sources
        """
        body = SourceQuery()
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
