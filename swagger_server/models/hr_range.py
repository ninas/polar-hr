# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class HRRange(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, min: int=None, max: int=None):  # noqa: E501
        """HRRange - a model defined in Swagger

        :param min: The min of this HRRange.  # noqa: E501
        :type min: int
        :param max: The max of this HRRange.  # noqa: E501
        :type max: int
        """
        self.swagger_types = {
            'min': int,
            'max': int
        }

        self.attribute_map = {
            'min': 'min',
            'max': 'max'
        }

        self._min = min
        self._max = max

    @classmethod
    def from_dict(cls, dikt) -> 'HRRange':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HRRange of this HRRange.  # noqa: E501
        :rtype: HRRange
        """
        return util.deserialize_model(dikt, cls)

    @property
    def min(self) -> int:
        """Gets the min of this HRRange.


        :return: The min of this HRRange.
        :rtype: int
        """
        return self._min

    @min.setter
    def min(self, min: int):
        """Sets the min of this HRRange.


        :param min: The min of this HRRange.
        :type min: int
        """

        self._min = min

    @property
    def max(self) -> int:
        """Gets the max of this HRRange.


        :return: The max of this HRRange.
        :rtype: int
        """
        return self._max

    @max.setter
    def max(self, max: int):
        """Sets the max of this HRRange.


        :param max: The max of this HRRange.
        :type max: int
        """

        self._max = max
