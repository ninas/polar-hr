import connexion
import six

from swagger_server.models.workout import Workout  # noqa: E501
from swagger_server.models.workout_query import WorkoutQuery  # noqa: E501
from swagger_server import util


def all_workouts():  # noqa: E501
    """Fetch all workouts

    Returns all workouts # noqa: E501


    :rtype: List[Workout]
    """
    return 'do some magic!'


def get_workout_by_id(workoutId, samples=None):  # noqa: E501
    """Retrieve a specific workout

    Returns a single workout # noqa: E501

    :param workoutId: ID of workout to return
    :type workoutId: int
    :param samples: Whether to include samples in return
    :type samples: bool

    :rtype: Workout
    """
    return 'do some magic!'


def search_for_workouts(body):  # noqa: E501
    """Search for workouts

    Search for workouts matching a variety of parameters. Using post due to length limitations on GET # noqa: E501

    :param body: Search for workouts
    :type body: dict | bytes

    :rtype: List[Workout]
    """
    if connexion.request.is_json:
        body = WorkoutQuery.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
