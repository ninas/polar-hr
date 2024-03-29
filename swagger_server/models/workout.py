# coding: utf-8

from __future__ import absolute_import, annotations

from datetime import date, datetime  # noqa: F401
from typing import Dict, List  # noqa: F401

import swagger_server.models.source as source
from swagger_server import util
from swagger_server.models.base_model_ import Model
from swagger_server.models.equipment import Equipment
from swagger_server.models.hr_zone import HRZone


class Workout(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(
        self,
        id: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        samples: List[int] = None,
        sport: str = None,
        calories: int = None,
        avg_hr: int = None,
        min_hr: int = None,
        max_hr: int = None,
        notes: str = None,
        equipment: List[Equipment] = None,
        sources: List[source.Source] = None,
        hr_zones: List[HRZone] = None,
    ):  # noqa: E501
        """Workout - a model defined in Swagger

        :param id: The id of this Workout.  # noqa: E501
        :type id: int
        :param start_time: The start_time of this Workout.  # noqa: E501
        :type start_time: datetime
        :param end_time: The end_time of this Workout.  # noqa: E501
        :type end_time: datetime
        :param samples: The samples of this Workout.  # noqa: E501
        :type samples: List[int]
        :param sport: The sport of this Workout.  # noqa: E501
        :type sport: str
        :param calories: The calories of this Workout.  # noqa: E501
        :type calories: int
        :param avg_hr: The avg_hr of this Workout.  # noqa: E501
        :type avg_hr: int
        :param min_hr: The min_hr of this Workout.  # noqa: E501
        :type min_hr: int
        :param max_hr: The max_hr of this Workout.  # noqa: E501
        :type max_hr: int
        :param notes: The notes of this Workout.  # noqa: E501
        :type notes: str
        :param equipment: The equipment of this Workout.  # noqa: E501
        :type equipment: List[Equipment]
        :param sources: The sources of this Workout.  # noqa: E501
        :type sources: List[source.Source]
        :param hr_zones: The hr_zones of this Workout.  # noqa: E501
        :type hr_zones: List[HRZone]
        """
        self.swagger_types = {
            "id": int,
            "start_time": datetime,
            "end_time": datetime,
            "samples": List[int],
            "sport": str,
            "calories": int,
            "avg_hr": int,
            "min_hr": int,
            "max_hr": int,
            "notes": str,
            "equipment": List[Equipment],
            "sources": List[source.Source],
            "hr_zones": List[HRZone],
        }

        self.attribute_map = {
            "id": "id",
            "start_time": "startTime",
            "end_time": "endTime",
            "samples": "samples",
            "sport": "sport",
            "calories": "calories",
            "avg_hr": "avgHR",
            "min_hr": "minHR",
            "max_hr": "maxHR",
            "notes": "notes",
            "equipment": "equipment",
            "sources": "sources",
            "hr_zones": "hrZones",
        }

        self._id = id
        self._start_time = start_time
        self._end_time = end_time
        self._samples = samples
        self._sport = sport
        self._calories = calories
        self._avg_hr = avg_hr
        self._min_hr = min_hr
        self._max_hr = max_hr
        self._notes = notes
        self._equipment = equipment
        self._sources = sources
        self._hr_zones = hr_zones

    @classmethod
    def from_dict(cls, dikt) -> "Workout":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Workout of this Workout.  # noqa: E501
        :rtype: Workout
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self) -> int:
        """Gets the id of this Workout.


        :return: The id of this Workout.
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id: int):
        """Sets the id of this Workout.


        :param id: The id of this Workout.
        :type id: int
        """

        self._id = id

    @property
    def start_time(self) -> datetime:
        """Gets the start_time of this Workout.


        :return: The start_time of this Workout.
        :rtype: datetime
        """
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: datetime):
        """Sets the start_time of this Workout.


        :param start_time: The start_time of this Workout.
        :type start_time: datetime
        """
        if start_time is None:
            raise ValueError(
                "Invalid value for `start_time`, must not be `None`"
            )  # noqa: E501

        self._start_time = start_time

    @property
    def end_time(self) -> datetime:
        """Gets the end_time of this Workout.


        :return: The end_time of this Workout.
        :rtype: datetime
        """
        return self._end_time

    @end_time.setter
    def end_time(self, end_time: datetime):
        """Sets the end_time of this Workout.


        :param end_time: The end_time of this Workout.
        :type end_time: datetime
        """

        self._end_time = end_time

    @property
    def samples(self) -> List[int]:
        """Gets the samples of this Workout.


        :return: The samples of this Workout.
        :rtype: List[int]
        """
        return self._samples

    @samples.setter
    def samples(self, samples: List[int]):
        """Sets the samples of this Workout.


        :param samples: The samples of this Workout.
        :type samples: List[int]
        """

        self._samples = samples

    @property
    def sport(self) -> str:
        """Gets the sport of this Workout.


        :return: The sport of this Workout.
        :rtype: str
        """
        return self._sport

    @sport.setter
    def sport(self, sport: str):
        """Sets the sport of this Workout.


        :param sport: The sport of this Workout.
        :type sport: str
        """

        self._sport = sport

    @property
    def calories(self) -> int:
        """Gets the calories of this Workout.


        :return: The calories of this Workout.
        :rtype: int
        """
        return self._calories

    @calories.setter
    def calories(self, calories: int):
        """Sets the calories of this Workout.


        :param calories: The calories of this Workout.
        :type calories: int
        """

        self._calories = calories

    @property
    def avg_hr(self) -> int:
        """Gets the avg_hr of this Workout.


        :return: The avg_hr of this Workout.
        :rtype: int
        """
        return self._avg_hr

    @avg_hr.setter
    def avg_hr(self, avg_hr: int):
        """Sets the avg_hr of this Workout.


        :param avg_hr: The avg_hr of this Workout.
        :type avg_hr: int
        """

        self._avg_hr = avg_hr

    @property
    def min_hr(self) -> int:
        """Gets the min_hr of this Workout.


        :return: The min_hr of this Workout.
        :rtype: int
        """
        return self._min_hr

    @min_hr.setter
    def min_hr(self, min_hr: int):
        """Sets the min_hr of this Workout.


        :param min_hr: The min_hr of this Workout.
        :type min_hr: int
        """

        self._min_hr = min_hr

    @property
    def max_hr(self) -> int:
        """Gets the max_hr of this Workout.


        :return: The max_hr of this Workout.
        :rtype: int
        """
        return self._max_hr

    @max_hr.setter
    def max_hr(self, max_hr: int):
        """Sets the max_hr of this Workout.


        :param max_hr: The max_hr of this Workout.
        :type max_hr: int
        """

        self._max_hr = max_hr

    @property
    def notes(self) -> str:
        """Gets the notes of this Workout.


        :return: The notes of this Workout.
        :rtype: str
        """
        return self._notes

    @notes.setter
    def notes(self, notes: str):
        """Sets the notes of this Workout.


        :param notes: The notes of this Workout.
        :type notes: str
        """

        self._notes = notes

    @property
    def equipment(self) -> List[Equipment]:
        """Gets the equipment of this Workout.


        :return: The equipment of this Workout.
        :rtype: List[Equipment]
        """
        return self._equipment

    @equipment.setter
    def equipment(self, equipment: List[Equipment]):
        """Sets the equipment of this Workout.


        :param equipment: The equipment of this Workout.
        :type equipment: List[Equipment]
        """

        self._equipment = equipment

    @property
    def sources(self) -> List[source.Source]:
        """Gets the sources of this Workout.


        :return: The sources of this Workout.
        :rtype: List[source.Source]
        """
        return self._sources

    @sources.setter
    def sources(self, sources: List[source.Source]):
        """Sets the sources of this Workout.


        :param sources: The sources of this Workout.
        :type sources: List[source.Source]
        """

        self._sources = sources

    @property
    def hr_zones(self) -> List[HRZone]:
        """Gets the hr_zones of this Workout.


        :return: The hr_zones of this Workout.
        :rtype: List[HRZone]
        """
        return self._hr_zones

    @hr_zones.setter
    def hr_zones(self, hr_zones: List[HRZone]):
        """Sets the hr_zones of this Workout.


        :param hr_zones: The hr_zones of this Workout.
        :type hr_zones: List[HRZone]
        """

        self._hr_zones = hr_zones
