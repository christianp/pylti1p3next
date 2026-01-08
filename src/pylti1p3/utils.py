import typing as t
import urllib.parse as urlparse  # type: ignore
from urllib.parse import urlencode  # type: ignore


def add_param_to_url(url: str, param_name: str, param_value: object) -> str:
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query[str(param_name)] = str(param_value)
    url_parts[4] = urlencode(query)
    return urlparse.urlunparse(url_parts)

def add_params_to_url(url: str, params: t.Dict[str, str]) -> str:
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    return urlparse.urlunparse(url_parts)
