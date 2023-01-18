# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server.models.source_type import SourceType
from swagger_server.models.workout import Workout
from swagger_server import util


class Source(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, id: int=None, url: str=None, name: str=None, creator: str=None, duration: str=None, source_type: SourceType=None, extra_info: str=None, tags: List[str]=None, exercises: List[str]=None, workouts: List[Workout]=None):  # noqa: E501
        """Source - a model defined in Swagger

        :param id: The id of this Source.  # noqa: E501
        :type id: int
        :param url: The url of this Source.  # noqa: E501
        :type url: str
        :param name: The name of this Source.  # noqa: E501
        :type name: str
        :param creator: The creator of this Source.  # noqa: E501
        :type creator: str
        :param duration: The duration of this Source.  # noqa: E501
        :type duration: str
        :param source_type: The source_type of this Source.  # noqa: E501
        :type source_type: SourceType
        :param extra_info: The extra_info of this Source.  # noqa: E501
        :type extra_info: str
        :param tags: The tags of this Source.  # noqa: E501
        :type tags: List[str]
        :param exercises: The exercises of this Source.  # noqa: E501
        :type exercises: List[str]
        :param workouts: The workouts of this Source.  # noqa: E501
        :type workouts: List[Workout]
        """
        self.swagger_types = {
            'id': int,
            'url': str,
            'name': str,
            'creator': str,
            'duration': str,
            'source_type': SourceType,
            'extra_info': str,
            'tags': List[str],
            'exercises': List[str],
            'workouts': List[Workout]
        }

        self.attribute_map = {
            'id': 'id',
            'url': 'url',
            'name': 'name',
            'creator': 'creator',
            'duration': 'duration',
            'source_type': 'sourceType',
            'extra_info': 'extraInfo',
            'tags': 'tags',
            'exercises': 'exercises',
            'workouts': 'workouts'
        }

        self._id = id
        self._url = url
        self._name = name
        self._creator = creator
        self._duration = duration
        self._source_type = source_type
        self._extra_info = extra_info
        self._tags = tags
        self._exercises = exercises
        self._workouts = workouts

    @classmethod
    def from_dict(cls, dikt) -> 'Source':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Source of this Source.  # noqa: E501
        :rtype: Source
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self) -> int:
        """Gets the id of this Source.


        :return: The id of this Source.
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id: int):
        """Sets the id of this Source.


        :param id: The id of this Source.
        :type id: int
        """

        self._id = id

    @property
    def url(self) -> str:
        """Gets the url of this Source.

        The descriptive and unique identifier for the source - may not actually be a web address  # noqa: E501

        :return: The url of this Source.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url: str):
        """Sets the url of this Source.

        The descriptive and unique identifier for the source - may not actually be a web address  # noqa: E501

        :param url: The url of this Source.
        :type url: str
        """
        if url is None:
            raise ValueError("Invalid value for `url`, must not be `None`")  # noqa: E501

        self._url = url

    @property
    def name(self) -> str:
        """Gets the name of this Source.


        :return: The name of this Source.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """Sets the name of this Source.


        :param name: The name of this Source.
        :type name: str
        """

        self._name = name

    @property
    def creator(self) -> str:
        """Gets the creator of this Source.


        :return: The creator of this Source.
        :rtype: str
        """
        return self._creator

    @creator.setter
    def creator(self, creator: str):
        """Sets the creator of this Source.


        :param creator: The creator of this Source.
        :type creator: str
        """

        self._creator = creator

    @property
    def duration(self) -> str:
        """Gets the duration of this Source.

        Duration in ISO 8601 format  # noqa: E501

        :return: The duration of this Source.
        :rtype: str
        """
        return self._duration

    @duration.setter
    def duration(self, duration: str):
        """Sets the duration of this Source.

        Duration in ISO 8601 format  # noqa: E501

        :param duration: The duration of this Source.
        :type duration: str
        """

        self._duration = duration

    @property
    def source_type(self) -> SourceType:
        """Gets the source_type of this Source.


        :return: The source_type of this Source.
        :rtype: SourceType
        """
        return self._source_type

    @source_type.setter
    def source_type(self, source_type: SourceType):
        """Sets the source_type of this Source.


        :param source_type: The source_type of this Source.
        :type source_type: SourceType
        """

        self._source_type = source_type

    @property
    def extra_info(self) -> str:
        """Gets the extra_info of this Source.

        Field that could be used to add sourceType specific info  # noqa: E501

        :return: The extra_info of this Source.
        :rtype: str
        """
        return self._extra_info

    @extra_info.setter
    def extra_info(self, extra_info: str):
        """Sets the extra_info of this Source.

        Field that could be used to add sourceType specific info  # noqa: E501

        :param extra_info: The extra_info of this Source.
        :type extra_info: str
        """

        self._extra_info = extra_info

    @property
    def tags(self) -> List[str]:
        """Gets the tags of this Source.


        :return: The tags of this Source.
        :rtype: List[str]
        """
        return self._tags

    @tags.setter
    def tags(self, tags: List[str]):
        """Sets the tags of this Source.


        :param tags: The tags of this Source.
        :type tags: List[str]
        """

        self._tags = tags

    @property
    def exercises(self) -> List[str]:
        """Gets the exercises of this Source.


        :return: The exercises of this Source.
        :rtype: List[str]
        """
        return self._exercises

    @exercises.setter
    def exercises(self, exercises: List[str]):
        """Sets the exercises of this Source.


        :param exercises: The exercises of this Source.
        :type exercises: List[str]
        """

        self._exercises = exercises

    @property
    def workouts(self) -> List[Workout]:
        """Gets the workouts of this Source.


        :return: The workouts of this Source.
        :rtype: List[Workout]
        """
        return self._workouts

    @workouts.setter
    def workouts(self, workouts: List[Workout]):
        """Sets the workouts of this Source.


        :param workouts: The workouts of this Source.
        :type workouts: List[Workout]
        """

        self._workouts = workouts
