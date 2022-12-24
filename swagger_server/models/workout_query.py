# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server.models.query import Query
from swagger_server import util


class WorkoutQuery(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, query: Query=None):  # noqa: E501
        """WorkoutQuery - a model defined in Swagger

        :param query: The query of this WorkoutQuery.  # noqa: E501
        :type query: Query
        """
        self.swagger_types = {
            'query': Query
        }

        self.attribute_map = {
            'query': 'query'
        }

        self._query = query

    @classmethod
    def from_dict(cls, dikt) -> 'WorkoutQuery':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The WorkoutQuery of this WorkoutQuery.  # noqa: E501
        :rtype: WorkoutQuery
        """
        return util.deserialize_model(dikt, cls)

    @property
    def query(self) -> Query:
        """Gets the query of this WorkoutQuery.


        :return: The query of this WorkoutQuery.
        :rtype: Query
        """
        return self._query

    @query.setter
    def query(self, query: Query):
        """Sets the query of this WorkoutQuery.


        :param query: The query of this WorkoutQuery.
        :type query: Query
        """

        self._query = query
