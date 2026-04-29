import typing as t
from .exception import SessionException
from .launch_data_storage.session import SessionDataStorage
from .request import Request
from .launch_data_storage.base import LaunchDataStorage


TStateParams = t.Dict[str, object]
TJwtBody = t.Mapping[str, t.Any]


class SessionService:
    data_storage: LaunchDataStorage[t.Any]
    _launch_data_lifetime = 86400
    _session_prefix = "lti1p3"

    """
    Handles storing and retrieving data to do with the user session.

    Use the subclass for your framework from the ``contrib`` package.
    """

    def __init__(self, request: Request):
        self.data_storage = SessionDataStorage()
        self.data_storage.set_request(request)

    def _get_key(
        self, key: str, nonce: t.Optional[str] = None, add_prefix: bool = True
    ):
        return (
            ((self._session_prefix + "-") if add_prefix else "")
            + key
            + (("-" + nonce) if nonce else "")
        )

    def _set_value(self, key: str, value: object):
        self.data_storage.set_value(key, value, exp=self._launch_data_lifetime)

    def _get_value(self, key: str) -> t.Any:
        return self.data_storage.get_value(key)

    def get_launch_data(self, key: str) -> TJwtBody:
        """
        Get cached launch data for the launch with the given ID.
        """
        return self._get_value(self._get_key(key, add_prefix=False))

    def save_launch_data(self, key: str, jwt_body: TJwtBody):
        """
        Save launch data to the cache, under the given ID.
        """
        self._set_value(self._get_key(key, add_prefix=False), jwt_body)

    def save_nonce(self, nonce: str):
        """
        Save an OIDC login nonce value to the cache.
        """
        self._set_value(self._get_key("nonce", nonce), True)

    def check_nonce(self, nonce: str) -> bool:
        """
        Check that a nonce value is valid: it's in the cache and hasn't expired.
        """
        nonce_key = self._get_key("nonce", nonce)
        return self.data_storage.check_value(nonce_key)

    def save_state_params(self, state: str, params: TStateParams):
        """
        Save custom OIDC login parameters to the cache.
        """
        self._set_value(self._get_key(state), params)

    def get_state_params(self, state: str) -> TStateParams:
        """
        Get custom OIDC login parameters from the cache.
        """
        return self._get_value(self._get_key(state))

    def set_state_valid(self, state: str, id_token_hash: str):
        """
        Save the hash of a launch ID token to the cache.
        """
        return self._set_value(self._get_key(state + "-id-token-hash"), id_token_hash)

    def check_state_is_valid(self, state: str, id_token_hash: str) -> bool:
        """
        Check that the LTI launch message's state is valid: it's in the cache and hasn't expired.
        """
        return self._get_value(self._get_key(state + "-id-token-hash")) == id_token_hash

    def set_data_storage(self, data_storage: LaunchDataStorage[t.Any]):
        """
        Set the data storage handler.
        Must be done before any values can be saved or retrieved.
        """
        self.data_storage = data_storage

    def set_launch_data_lifetime(self, time_sec: int):
        """
        Set the lifetime for values saved to storage, in seconds.
        """
        if self.data_storage.can_set_keys_expiration():
            self._launch_data_lifetime = time_sec
        else:
            raise SessionException(
                f"{self.data_storage.__class__.__name__} launch storage doesn't support "
                f"changing the expiration time of keys"
            )
