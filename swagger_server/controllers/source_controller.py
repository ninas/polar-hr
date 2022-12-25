import connexion
import six

from swagger_server.models.source import Source  # noqa: E501
from swagger_server.models.source_query import SourceQuery  # noqa: E501
from swagger_server import util


def get_sources(id=None, url=None):  # noqa: E501
    """Retrieve a specific source using its id or all if no ids are specified

    Returns sources # noqa: E501

    :param id: ID of source to return
    :type id: List[int]
    :param url: URL of source to return
    :type url: List[int]

    :rtype: Source
    """
    return 'do some magic!'


def search_for_sources(body):  # noqa: E501
    """Search for sources

    Search for sources matching a variety of parameters. Using post due to length limitations on GET # noqa: E501

    :param body: Search for sources
    :type body: dict | bytes

    :rtype: List[Source]
    """
    if connexion.request.is_json:
        body = SourceQuery.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
