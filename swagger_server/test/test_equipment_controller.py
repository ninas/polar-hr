# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.test import BaseTestCase


class TestEquipmentController(BaseTestCase):
    """EquipmentController integration test stubs"""

    def test_all_equipment(self):
        """Test case for all_equipment

        Return all equipment
        """
        response = self.client.open(
            '/NINASCHIFF/workout-api/1.0.0/equipment',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
