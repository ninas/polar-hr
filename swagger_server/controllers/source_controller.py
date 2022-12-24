import connexion
import six

from swagger_server.models.source import Source  # noqa: E501
from swagger_server.models.source_query import SourceQuery  # noqa: E501
from swagger_server import util


def all_sources():  # noqa: E501
    """Return all sources

    Fetch all sources # noqa: E501


    :rtype: List[Source]
    """
    return 'do some magic!'


def get_source_by_id(sourceId):  # noqa: E501
    """Retrieve a specific source using its id

    Returns a single source # noqa: E501

    :param sourceId: ID of source to return
    :type sourceId: int

    :rtype: Source
    """
    return 'do some magic!'


def get_source_by_url(sourceUrl):  # noqa: E501
    """Retrieve a specific source using its url

    Returns a single source # noqa: E501

    :param sourceUrl: URL of source to return
    :type sourceUrl: str

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
