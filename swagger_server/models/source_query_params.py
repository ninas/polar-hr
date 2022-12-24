# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server.models.source_type import SourceType
from swagger_server import util


class SourceQueryParams(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, creator: List[str]=None, exercises: List[str]=None, tags: List[str]=None, tag_types: List[str]=None, length_min: int=None, length_max: int=None, source_type: List[SourceType]=None):  # noqa: E501
        """SourceQueryParams - a model defined in Swagger

        :param creator: The creator of this SourceQueryParams.  # noqa: E501
        :type creator: List[str]
        :param exercises: The exercises of this SourceQueryParams.  # noqa: E501
        :type exercises: List[str]
        :param tags: The tags of this SourceQueryParams.  # noqa: E501
        :type tags: List[str]
        :param tag_types: The tag_types of this SourceQueryParams.  # noqa: E501
        :type tag_types: List[str]
        :param length_min: The length_min of this SourceQueryParams.  # noqa: E501
        :type length_min: int
        :param length_max: The length_max of this SourceQueryParams.  # noqa: E501
        :type length_max: int
        :param source_type: The source_type of this SourceQueryParams.  # noqa: E501
        :type source_type: List[SourceType]
        """
        self.swagger_types = {
            'creator': List[str],
            'exercises': List[str],
            'tags': List[str],
            'tag_types': List[str],
            'length_min': int,
            'length_max': int,
            'source_type': List[SourceType]
        }

        self.attribute_map = {
            'creator': 'creator',
            'exercises': 'exercises',
            'tags': 'tags',
            'tag_types': 'tagTypes',
            'length_min': 'lengthMin',
            'length_max': 'lengthMax',
            'source_type': 'sourceType'
        }

        self._creator = creator
        self._exercises = exercises
        self._tags = tags
        self._tag_types = tag_types
        self._length_min = length_min
        self._length_max = length_max
        self._source_type = source_type

    @classmethod
    def from_dict(cls, dikt) -> 'SourceQueryParams':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The SourceQueryParams of this SourceQueryParams.  # noqa: E501
        :rtype: SourceQueryParams
        """
        return util.deserialize_model(dikt, cls)

    @property
    def creator(self) -> List[str]:
        """Gets the creator of this SourceQueryParams.

        Filter by source creator  # noqa: E501

        :return: The creator of this SourceQueryParams.
        :rtype: List[str]
        """
        return self._creator

    @creator.setter
    def creator(self, creator: List[str]):
        """Sets the creator of this SourceQueryParams.

        Filter by source creator  # noqa: E501

        :param creator: The creator of this SourceQueryParams.
        :type creator: List[str]
        """

        self._creator = creator

    @property
    def exercises(self) -> List[str]:
        """Gets the exercises of this SourceQueryParams.

        Return workouts which used a source containing this exercise  # noqa: E501

        :return: The exercises of this SourceQueryParams.
        :rtype: List[str]
        """
        return self._exercises

    @exercises.setter
    def exercises(self, exercises: List[str]):
        """Sets the exercises of this SourceQueryParams.

        Return workouts which used a source containing this exercise  # noqa: E501

        :param exercises: The exercises of this SourceQueryParams.
        :type exercises: List[str]
        """

        self._exercises = exercises

    @property
    def tags(self) -> List[str]:
        """Gets the tags of this SourceQueryParams.

        Tags to filter by  # noqa: E501

        :return: The tags of this SourceQueryParams.
        :rtype: List[str]
        """
        return self._tags

    @tags.setter
    def tags(self, tags: List[str]):
        """Sets the tags of this SourceQueryParams.

        Tags to filter by  # noqa: E501

        :param tags: The tags of this SourceQueryParams.
        :type tags: List[str]
        """

        self._tags = tags

    @property
    def tag_types(self) -> List[str]:
        """Gets the tag_types of this SourceQueryParams.

        Filter by specific type of tag  # noqa: E501

        :return: The tag_types of this SourceQueryParams.
        :rtype: List[str]
        """
        return self._tag_types

    @tag_types.setter
    def tag_types(self, tag_types: List[str]):
        """Sets the tag_types of this SourceQueryParams.

        Filter by specific type of tag  # noqa: E501

        :param tag_types: The tag_types of this SourceQueryParams.
        :type tag_types: List[str]
        """

        self._tag_types = tag_types

    @property
    def length_min(self) -> int:
        """Gets the length_min of this SourceQueryParams.

        Minimum length of a source  # noqa: E501

        :return: The length_min of this SourceQueryParams.
        :rtype: int
        """
        return self._length_min

    @length_min.setter
    def length_min(self, length_min: int):
        """Sets the length_min of this SourceQueryParams.

        Minimum length of a source  # noqa: E501

        :param length_min: The length_min of this SourceQueryParams.
        :type length_min: int
        """

        self._length_min = length_min

    @property
    def length_max(self) -> int:
        """Gets the length_max of this SourceQueryParams.

        Maximum length of a source  # noqa: E501

        :return: The length_max of this SourceQueryParams.
        :rtype: int
        """
        return self._length_max

    @length_max.setter
    def length_max(self, length_max: int):
        """Sets the length_max of this SourceQueryParams.

        Maximum length of a source  # noqa: E501

        :param length_max: The length_max of this SourceQueryParams.
        :type length_max: int
        """

        self._length_max = length_max

    @property
    def source_type(self) -> List[SourceType]:
        """Gets the source_type of this SourceQueryParams.


        :return: The source_type of this SourceQueryParams.
        :rtype: List[SourceType]
        """
        return self._source_type

    @source_type.setter
    def source_type(self, source_type: List[SourceType]):
        """Sets the source_type of this SourceQueryParams.


        :param source_type: The source_type of this SourceQueryParams.
        :type source_type: List[SourceType]
        """

        self._source_type = source_type
