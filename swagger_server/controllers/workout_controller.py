import connexion
import six

from swagger_server.models.paginated_result import PaginatedResult  # noqa: E501
from swagger_server.models.query import Query  # noqa: E501
from swagger_server import util


def get_workouts(id=None, includeSamples=None, paginate=None, paginationId=None):  # noqa: E501
    """Retrieve a specific workout or all if no ids are specified

    Returns workouts # noqa: E501

    :param id: ID of workout to return
    :type id: List[int]
    :param includeSamples: Whether to include samples in return
    :type includeSamples: bool
    :param paginate: Paginate results
    :type paginate: bool
    :param paginationId: ID of next page to return. If not set, but paginate is True, the first page will be returned (and will include the ID of the next page). If this is set, it supersedes any value passed as paginate.
    :type paginationId: int

    :rtype: PaginatedResult
    """
    return 'do some magic!'


def search_for_workouts(body):  # noqa: E501
    """Search for workouts

    Search for workouts matching a variety of parameters. Using post due to length limitations on GET # noqa: E501

    :param body: Search for workouts
    :type body: dict | bytes

    :rtype: PaginatedResult
    """
    if connexion.request.is_json:
        body = Query.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
