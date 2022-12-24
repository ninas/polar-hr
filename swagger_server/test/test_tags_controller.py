# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.tag import Tag  # noqa: E501
from swagger_server.test import BaseTestCase


class TestTagsController(BaseTestCase):
    """TagsController integration test stubs"""

    def test_all_tags(self):
        """Test case for all_tags

        Return all tags
        """
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/tags',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
