import connexion
import six

from swagger_server.models.paginated_result import PaginatedResult  # noqa: E501
from swagger_server import util


def everything():  # noqa: E501
    """Return all data

    Fetch everything # noqa: E501


    :rtype: PaginatedResult
    """
    return 'do some magic!'


def refresh():  # noqa: E501
    """Refresh workout data

    Manually refresh workout data # noqa: E501


    :rtype: None
    """
    return 'do some magic!'
