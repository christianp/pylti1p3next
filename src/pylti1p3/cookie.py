import typing as t
from abc import ABCMeta, abstractmethod


class CookieService:
    """ An interface for setting and getting cookie data. """

    __metaclass__ = ABCMeta
    _cookie_prefix: str = "lti1p3"

    @abstractmethod
    def get_cookie(self, name: str) -> t.Optional[str]:
        """ Get the cookie with the given name, or ``None`` if it doesn't exist. """
        raise NotImplementedError

    @abstractmethod
    def set_cookie(
        self, name: str, value: t.Union[str, int], exp: t.Optional[int] = 3600
    ):
        """ 
            Set a cookie with the given name and value.

            The expiry time of the cookie is measured in seconds.
        """
        raise NotImplementedError
