# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server.models.zone_type import ZoneType
from swagger_server import util


class HRZoneAbove(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, zone_type: ZoneType=None, min_time: str=None, percent_spent_above: float=None):  # noqa: E501
        """HRZoneAbove - a model defined in Swagger

        :param zone_type: The zone_type of this HRZoneAbove.  # noqa: E501
        :type zone_type: ZoneType
        :param min_time: The min_time of this HRZoneAbove.  # noqa: E501
        :type min_time: str
        :param percent_spent_above: The percent_spent_above of this HRZoneAbove.  # noqa: E501
        :type percent_spent_above: float
        """
        self.swagger_types = {
            'zone_type': ZoneType,
            'min_time': str,
            'percent_spent_above': float
        }

        self.attribute_map = {
            'zone_type': 'zoneType',
            'min_time': 'minTime',
            'percent_spent_above': 'percentSpentAbove'
        }

        self._zone_type = zone_type
        self._min_time = min_time
        self._percent_spent_above = percent_spent_above

    @classmethod
    def from_dict(cls, dikt) -> 'HRZoneAbove':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HRZoneAbove of this HRZoneAbove.  # noqa: E501
        :rtype: HRZoneAbove
        """
        return util.deserialize_model(dikt, cls)

    @property
    def zone_type(self) -> ZoneType:
        """Gets the zone_type of this HRZoneAbove.


        :return: The zone_type of this HRZoneAbove.
        :rtype: ZoneType
        """
        return self._zone_type

    @zone_type.setter
    def zone_type(self, zone_type: ZoneType):
        """Sets the zone_type of this HRZoneAbove.


        :param zone_type: The zone_type of this HRZoneAbove.
        :type zone_type: ZoneType
        """

        self._zone_type = zone_type

    @property
    def min_time(self) -> str:
        """Gets the min_time of this HRZoneAbove.

        Duration in ISO 8601 format  # noqa: E501

        :return: The min_time of this HRZoneAbove.
        :rtype: str
        """
        return self._min_time

    @min_time.setter
    def min_time(self, min_time: str):
        """Sets the min_time of this HRZoneAbove.

        Duration in ISO 8601 format  # noqa: E501

        :param min_time: The min_time of this HRZoneAbove.
        :type min_time: str
        """

        self._min_time = min_time

    @property
    def percent_spent_above(self) -> float:
        """Gets the percent_spent_above of this HRZoneAbove.

        This will supercede any other parameters passed. Percentage of workout spent in this HRZone or higher  # noqa: E501

        :return: The percent_spent_above of this HRZoneAbove.
        :rtype: float
        """
        return self._percent_spent_above

    @percent_spent_above.setter
    def percent_spent_above(self, percent_spent_above: float):
        """Sets the percent_spent_above of this HRZoneAbove.

        This will supercede any other parameters passed. Percentage of workout spent in this HRZone or higher  # noqa: E501

        :param percent_spent_above: The percent_spent_above of this HRZoneAbove.
        :type percent_spent_above: float
        """

        self._percent_spent_above = percent_spent_above
