import base64
import hashlib
import json
import typing as t
import uuid
from abc import ABCMeta, abstractmethod

import jwt  # type: ignore
import requests
import typing_extensions as te
from jwcrypto.jwk import JWK  # type: ignore

from .actions import Action
from .assignments_grades import AssignmentsGradesService, TAssignmentsGradersData
from .cookie import CookieService
from .course_groups import CourseGroupsService, TGroupsServiceData
from .deep_link import DeepLink, TDeepLinkData
from .exception import (
    LtiException,
    LtiJWTException,
    LtiMessageValidationException,
    LtiInvalidNonceException,
    LtiKeyException,
)
from .launch_data_storage.base import DisableSessionId, LaunchDataStorage
from .message_validators import get_validators
from .message_validators.deep_link import DeepLinkMessageValidator
from .message_validators.privacy_launch import PrivacyLaunchValidator
from .message_validators.resource_message import ResourceMessageValidator
from .message_validators.submission_review import SubmissionReviewLaunchValidator
from .names_roles import NamesRolesProvisioningService, TNamesAndRolesData
from .roles import (
    StaffRole,
    StudentRole,
    TeacherRole,
    TeachingAssistantRole,
    DesignerRole,
    ObserverRole,
    TransientRole,
)
from .registration import Registration, TKeySet
from .request import Request
from .session import SessionService
from .service_connector import ServiceConnector, REQUESTS_USER_AGENT
from .tool_config import ToolConfAbstract

#: A claim describing the resource link used to make the launch.
TResourceLinkClaim = te.TypedDict(
    "TResourceLinkClaim",
    {
        # Required data
        "id": str,
        # Optional data
        "description": str,
        "title": str,
    },
    total=False,
)

#: A claim describing the context of the launch.
TContextClaim = te.TypedDict(
    "TContextClaim",
    {
        # Required data
        "id": str,
        # Optional data
        "label": str,
        "title": str,
        "type": t.List[str],
    },
    total=False,
)

#: A claim describing the platform used to make the launch.
TToolPlatformClaim = te.TypedDict(
    "TToolPlatformClaim",
    {
        # Required data
        "guid": str,
        # Optional data
        "contact_email": str,
        "description": str,
        "name": str,
        "url": str,
        "product_family_code": str,
        "version": str,
    },
    total=False,
)

#: A claim describing the person's Learning Information Services data.
TLearningInformationServicesClaim = te.TypedDict(
    "TLearningInformationServicesClaim",
    {
        "person_sourcedid": str,
        "course_offering_sourcedid": str,
        "course_section_sourcedid": str,
    },
    total=False,
)

#: A claim describing a link migrated from LTI 1.1.
TMigrationClaim = te.TypedDict(
    "TMigrationClaim",
    {
        # Required data
        "oauth_consumer_key": str,
        # Optional data
        "oauth_consumer_key_sign": str,
        "user_id": str,
        "context_id": str,
        "tool_consumer_instance_guid ": str,
        "resource_link_id": str,
    },
    total=False,
)

#: A claim describing the user the launch was made for, given during submission review or data privacy launches.
TForUserClaim = te.TypedDict(
    "TForUserClaim",
    {
        # Required data
        "user_id": str,
        # Optional data
        "person_sourcedId": str,
        "given_name": str,
        "family_name": str,
        "name": str,
        "email": str,
        "roles": t.List[str],
    },
)

#: The data passed in the launch message.
TLaunchData = te.TypedDict(
    "TLaunchData",
    {
        # Required data
        "iss": str,
        "nonce": str,
        "aud": t.Union[t.List[str], str],
        "https://purl.imsglobal.org/spec/lti/claim/message_type": te.Literal[
            "LtiResourceLinkRequest",
            "LtiDeepLinkingRequest",
            "DataPrivacyLaunchRequest",
            "LtiSubmissionReviewRequest",
        ],
        "https://purl.imsglobal.org/spec/lti/claim/version": te.Literal["1.3.0"],
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": str,
        "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": str,
        "https://purl.imsglobal.org/spec/lti/claim/resource_link": TResourceLinkClaim,
        "https://purl.imsglobal.org/spec/lti/claim/roles": t.List[str],
        "sub": str,
        # Optional data
        "given_name": str,
        "family_name": str,
        "name": str,
        "email": str,
        "https://purl.imsglobal.org/spec/lti/claim/context": TContextClaim,
        "https://purl.imsglobal.org/spec/lti/claim/lis": TLearningInformationServicesClaim,
        "https://purl.imsglobal.org/spec/lti/claim/custom": t.Mapping[str, str],
        "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings": TDeepLinkData,
        "https://purl.imsglobal.org/spec/lti-gs/claim/groupsservice": TGroupsServiceData,
        "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice": TNamesAndRolesData,
        "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint": TAssignmentsGradersData,
        "https://purl.imsglobal.org/spec/lti/claim/tool_platform": TToolPlatformClaim,
        "https://purl.imsglobal.org/spec/lti/claim/role_scope_mentor": t.List[str],
        "https://purl.imsglobal.org/spec/lti/claim/lti1p1": TMigrationClaim,
        "https://purl.imsglobal.org/spec/lti/claim/for_user": TForUserClaim,
    },
    total=False,
)

#: Data from the JWT header.
TJwtHeader = te.TypedDict(
    "TJwtHeader",
    {
        "kid": str,
        "alg": str,
    },
    total=False,
)

#: JWT response data.
TJwtData = te.TypedDict(
    "TJwtData",
    {
        "header": TJwtHeader,
        "body": TLaunchData,
    },
    total=False,
)

REQ = t.TypeVar("REQ", bound=Request)
TCONF = t.TypeVar("TCONF", bound=ToolConfAbstract)
SES = t.TypeVar("SES", bound=SessionService)
COOK = t.TypeVar("COOK", bound=CookieService)


class MessageLaunch(t.Generic[REQ, TCONF, SES, COOK]):
    """ Stores data from an LTI launch and provides methods to interact with LTI services. """

    __metaclass__ = ABCMeta
    _request: REQ
    _tool_config: TCONF
    _session_service: SES
    _cookie_service: COOK
    _jwt: TJwtData
    _jwt_verify_options: t.Dict[str, bool]
    _registration: t.Optional[Registration]
    _launch_id: str
    _validated: bool = False
    _auto_validation: bool = True
    _restored: bool = False
    _id_token_hash: t.Optional[str]
    _public_key_cache_data_storage: t.Optional[LaunchDataStorage[t.Any]] = None
    _public_key_cache_lifetime: t.Optional[int] = None

    def __init__(
        self,
        request: REQ,
        tool_config: TCONF,
        *,
        session_service: t.Optional[SES] = None,
        cookie_service: t.Optional[COOK] = None,
        launch_data_storage: t.Optional[LaunchDataStorage[t.Any]] = None,
        requests_session: t.Optional[requests.Session] = None,
        service_connector_cls: type[ServiceConnector] = ServiceConnector,
    ):
        self._request = request
        self._tool_config = tool_config

        assert session_service is not None, "Session Service must be set"
        assert cookie_service is not None, "Cookie Service must be set"

        self._session_service = session_service
        self._cookie_service = cookie_service
        self._launch_id = "lti1p3-launch-" + str(uuid.uuid4())
        self._jwt = {}
        self._jwt_verify_options = {"verify_aud": False}
        self._id_token_hash = None
        self._validated = False
        self._auto_validation = True
        self._restored = False
        self._public_key_cache_data_storage = None
        self._public_key_cache_lifetime = None
        self._service_connector_cls = service_connector_cls
        if requests_session:
            self._requests_session = requests_session
        else:
            self._requests_session = requests.Session()
            self._requests_session.headers["User-Agent"] = REQUESTS_USER_AGENT

        if launch_data_storage:
            self.set_launch_data_storage(launch_data_storage)

    @abstractmethod
    def _get_request_param(self, key: str) -> str:
        raise NotImplementedError

    def set_launch_id(self, launch_id: str) -> "MessageLaunch":
        """
            Set the launch's ID.
        """
        self._launch_id = launch_id
        return self

    def set_auto_validation(self, enable: bool) -> "MessageLaunch":
        """
            Enable or disable automatic validation of the body of the launch message JWT.

            If enabled, the data will be validated and cached on access.
        """
        self._auto_validation = enable
        return self

    def set_jwt(self, val: TJwtData) -> "MessageLaunch":
        """
            Store the JWT data for this launch.
        """
        self._jwt = val
        return self

    def set_jwt_verify_options(self, val: t.Dict[str, bool]) -> "MessageLaunch":
        """
            Set the JWT verification options.
        """
        self._jwt_verify_options = val
        return self

    def set_restored(self) -> "MessageLaunch":
        """
            Mark this launch as restored from cache.
        """
        self._restored = True
        return self

    def get_session_service(self) -> SES:
        """
            Get a handler for the session service.
        """
        return self._session_service

    def get_iss(self) -> str:
        """
            Get the launch's issuer. (the ``iss`` property)
        """
        iss = self._get_jwt_body().get("iss")
        if not iss:
            raise LtiMessageValidationException(
                'The "iss" field in the launch message is empty.'
            )
        return iss

    def get_client_id(self) -> str:
        """
            Get the client ID of the launch. (the ``aud`` property)
        """
        jwt_body = self._get_jwt_body()
        aud = jwt_body.get("aud")
        return aud[0] if isinstance(aud, list) else aud  # type: ignore

    @classmethod
    def from_cache(
        cls,
        launch_id: str,
        request: REQ,
        tool_config: TCONF,
        *,
        session_service: t.Optional[SES] = None,
        cookie_service: t.Optional[COOK] = None,
        launch_data_storage: t.Optional[LaunchDataStorage[t.Any]] = None,
        requests_session: t.Optional[requests.Session] = None,
        service_connector_cls: type[ServiceConnector] = ServiceConnector,
    ) -> "MessageLaunch":
        """
            Restore a launch message from the cache, using the launch ID.
        """
        obj = cls(
            request,
            tool_config,
            session_service=session_service,
            cookie_service=cookie_service,
            launch_data_storage=launch_data_storage,
            requests_session=requests_session,
            service_connector_cls=service_connector_cls,
        )
        launch_data = obj.get_session_service().get_launch_data(launch_id)
        if not launch_data:
            raise LtiException("Could not find LTI launch data in the session service.")
        return (
            obj.set_launch_id(launch_id)
            .set_auto_validation(enable=False)
            .set_jwt(t.cast(TJwtData, {"body": launch_data}))
            .set_restored()
            .validate_registration()
        )

    def validate(self) -> "MessageLaunch":
        """
        Validates all aspects of an incoming LTI message launch and caches the launch if successful.
        """
        if self._restored:
            raise LtiMessageValidationException("A restored launch can't be validated.")
        self._validated = True
        try:
            return (
                self.validate_state()
                .validate_jwt_format()
                .validate_nonce()
                .validate_registration()
                .validate_jwt_signature()
                .validate_deployment()
                .validate_message()
                .save_launch_data()
            )
        except Exception:
            self._validated = False
            raise

    def _get_jwt_body(self) -> TLaunchData:
        if not self._validated and self._auto_validation:
            self.validate()
        return self._jwt.get("body", {})

    def _get_iss(self) -> str:
        iss = self._get_jwt_body().get("iss")
        if not iss:
            raise LtiMessageValidationException(
                'The LTI launch message "iss" field is empty.'
            )
        return iss

    def _get_id_token(self) -> str:
        id_token = self._get_request_param("id_token")
        if not id_token:
            raise LtiMessageValidationException(
                'The LTI launch message "id_token" field is empty.'
            )
        return id_token

    def _get_id_token_hash(self) -> str:
        if not self._id_token_hash:
            id_token = self._get_id_token()
            id_token_param = id_token.encode("utf8")
            self._id_token_hash = hashlib.md5(id_token_param).hexdigest()
        return self._id_token_hash

    def _get_deployment_id(self) -> str:
        deployment_id = self._get_jwt_body().get(
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
        )
        if not deployment_id:
            raise LtiMessageValidationException(
                'The "deployment_id" field is not set in the launch message\'s JWT body.'
            )
        return deployment_id

    def get_service_connector(self) -> ServiceConnector:
        """
            Get a service connector instance for this launch's registration and session.
        """
        assert self._registration is not None, "Registration not yet set"
        return self._service_connector_cls(self._registration, self._requests_session)

    def has_nrps(self) -> bool:
        """
        Returns whether or not the current launch can use the names and roles service.
        """
        return (
            self._get_jwt_body()
            .get("https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice", {})
            .get("context_memberships_url", None)
            is not None
        )

    def get_nrps(self) -> NamesRolesProvisioningService:
        """
        Fetches an instance of the names and roles service for the current launch.
        """
        assert self._registration is not None, "Registration not yet set"
        connector = self.get_service_connector()
        names_role_service = self._get_jwt_body().get(
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice"
        )
        if not names_role_service:
            raise LtiJWTException(
                'The "namesroleservice" field is not set in the launch message\'s JWT body.'
            )
        return NamesRolesProvisioningService(connector, names_role_service)

    def has_ags(self) -> bool:
        """
        Returns whether or not the current launch can use the assignments and grades service.
        """
        return (
            self._get_jwt_body().get(
                "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint", None
            )
            is not None
        )

    def get_ags(self) -> AssignmentsGradesService:
        """
        Returns a handler for the assignments and grades service for the current launch.
        """
        assert self._registration is not None, "Registration not yet set"
        connector = self.get_service_connector()
        endpoint = self._get_jwt_body().get(
            "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint"
        )
        if not endpoint:
            raise LtiJWTException('The "endpoint" field is not set.')
        return AssignmentsGradesService(connector, endpoint)

    def has_cgs(self) -> bool:
        """
        Returns whether or not the current launch can use the course groups service.
        """
        groups_service_data = self._get_jwt_body().get(
            "https://purl.imsglobal.org/spec/lti-gs/claim/groupsservice", {}
        )
        return groups_service_data.get("context_groups_url", None) is not None

    def get_cgs(self) -> CourseGroupsService:
        """
        Returns a handler for the course groups service for the current launch.
        """
        assert self._registration is not None, "Registration not yet set"
        connector = self.get_service_connector()
        groups_service_data = self._get_jwt_body().get(
            "https://purl.imsglobal.org/spec/lti-gs/claim/groupsservice"
        )
        if not groups_service_data:
            raise LtiJWTException('The "groupsservice" field is not set.')
        context_groups_url = groups_service_data.get("context_groups_url", None)
        if not context_groups_url:
            raise LtiJWTException(
                'The "context_groups_url" field is not set in the groupsservice section.'
            )
        return CourseGroupsService(connector, groups_service_data)

    def get_deep_link(self) -> DeepLink:
        """
        Returns a deep link handler that can be used to construct a deep linking response.
        """
        assert self._registration is not None, "Registration not yet set"

        deployment_id = self._get_deployment_id()
        deep_linking_settings = self._get_jwt_body().get(
            "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"
        )
        if not deep_linking_settings:
            raise LtiJWTException('The "deep_linking_settings" field is not set.')

        return DeepLink(self._registration, deployment_id, deep_linking_settings)

    def get_data_privacy_launch_user(self) -> t.Optional[TForUserClaim]:
        """
        Applicable for ``DataPrivacyLaunchRequest`` only. Returns information about user
        whose data the launch is intended to action upon, for instance the student
        who has requested their data be removed under GDPR's right to be forgotten.
        """
        jwt_body = self._get_jwt_body()
        return jwt_body.get("https://purl.imsglobal.org/spec/lti/claim/for_user")

    def get_submission_review_user(self) -> t.Optional[TForUserClaim]:
        """
        Applicable for ``LtiSubmissionReviewRequest`` only. Returns information about user
        whose submission should be displayed for review.
        """
        jwt_body = self._get_jwt_body()
        return jwt_body.get("https://purl.imsglobal.org/spec/lti/claim/for_user")

    def is_deep_link_launch(self) -> bool:
        """
        Returns whether or not the current launch is a deep linking launch.
        """
        jwt_body = self._get_jwt_body()
        return DeepLinkMessageValidator().can_validate(jwt_body)

    def is_resource_launch(self) -> bool:
        """
        Returns whether or not the current launch is a resource launch.
        """
        jwt_body = self._get_jwt_body()
        return ResourceMessageValidator().can_validate(jwt_body)

    def is_data_privacy_launch(self) -> bool:
        """
        Returns whether or not the current launch is a data privacy launch.
        """
        jwt_body = self._get_jwt_body()
        return PrivacyLaunchValidator().can_validate(jwt_body)

    def is_submission_review_launch(self) -> bool:
        """
        Returns whether or not the current launch is a submission review launch.
        """
        jwt_body = self._get_jwt_body()
        return SubmissionReviewLaunchValidator().can_validate(jwt_body)

    def get_launch_data(self) -> TLaunchData:
        """
        Fetches the decoded body of the JWT used in the current launch.
        """
        return self._get_jwt_body()

    def get_launch_id(self) -> str:
        """
        Get the unique launch ID for the current launch, used to refer to the launch in subsequent requests.
        """
        return self._launch_id

    def get_tool_conf(self) -> TCONF:
        """
        Get the tool config object for this launch.
        """
        return self._tool_config

    @staticmethod
    def urlsafe_b64decode(val: str) -> str:
        """
        Decode a URL-safe base 64 string.
        """
        # TODO - move this to the utils package? Is this already in the standard library?
        remainder = len(val) % 4
        if remainder > 0:
            padlen = 4 - remainder
            val = val + ("=" * padlen)
        tmp = val.translate(str.maketrans("-_", "+/"))  # type: ignore
        return base64.b64decode(tmp).decode("utf-8")  # type: ignore

    def set_public_key_caching(
        self, data_storage: LaunchDataStorage[t.Any], cache_lifetime: int = 7200
    ):
        """
        Set the public key caching settings.

        ``cache_lifetime`` is measured in seconds.
        """
        self._public_key_cache_data_storage = data_storage
        self._public_key_cache_lifetime = cache_lifetime

    def fetch_public_key(self, key_set_url: str) -> TKeySet:
        """
        Fetch the public key from the given URL, using the cache if possible.
        """
        cache_key = (
            "key-set-url-" + hashlib.md5(key_set_url.encode("utf-8")).hexdigest()
        )

        with DisableSessionId(self._public_key_cache_data_storage):
            if self._public_key_cache_data_storage:
                public_key = self._public_key_cache_data_storage.get_value(cache_key)
                if public_key:
                    return public_key

            try:
                resp = self._requests_session.get(key_set_url)
            except requests.exceptions.RequestException as e:
                raise LtiKeyException(
                    f"Error while fetching the public key URL {key_set_url}: {str(e)}"
                ) from e
            try:
                public_key = resp.json()
                if self._public_key_cache_data_storage:
                    self._public_key_cache_data_storage.set_value(
                        cache_key, public_key, self._public_key_cache_lifetime
                    )
                return public_key
            except ValueError as e:
                raise LtiKeyException(
                    f"Invalid response while fetching the platform's public key from {key_set_url}."
                    f"Must be JSON: {resp.text}"
                ) from e

    def get_public_key(self) -> t.Tuple[str, str]:
        """
        Get the platform's public key for this launch.
        """
        assert self._registration is not None, "Registration not yet set"
        public_key_set = self._registration.get_key_set()
        key_set_url = self._registration.get_key_set_url()

        if not public_key_set:
            assert (
                key_set_url is not None
            ), "If public_key_set is not set, public_set_url should be set"
            if key_set_url.startswith(("http://", "https://")):
                public_key_set = self.fetch_public_key(key_set_url)
                self._registration.set_key_set(public_key_set)
            else:
                raise LtiKeyException(
                    "The public key set URL is invalid: " + key_set_url
                )

        # Find key used to sign the JWT (matches the KID in the header)
        kid = self._jwt.get("header", {}).get("kid", None)
        alg = self._jwt.get("header", {}).get("alg", None)

        if not kid:
            raise LtiKeyException("JWT KID not found")
        if not alg:
            raise LtiKeyException("JWT ALG not found")

        for key in public_key_set["keys"]:
            key_kid = key.get("kid")
            key_alg = key.get("alg", "RS256")
            if key_kid and key_kid == kid and key_alg == alg:
                try:
                    key_json = json.dumps(key)
                    jwk_obj = JWK.from_json(key_json)
                    public_key = jwk_obj.export_to_pem()
                    return public_key, key_alg
                except (ValueError, TypeError) as e:
                    raise LtiKeyException("Can't convert JWT key to PEM format") from e

        # Could not find public key with a matching kid and alg.
        raise LtiKeyException("Unable to find public key")

    def validate_state(self) -> "MessageLaunch":
        """
        Validate the launch message's ``state`` parameter.

        See https://www.rfc-editor.org/rfc/rfc6749#section-10.12
        """
        state_from_request = self._get_request_param("state")
        if not state_from_request:
            raise LtiMessageValidationException("Missing state param")

        id_token_hash = self._get_id_token_hash()
        if not self._session_service.check_state_is_valid(
            state_from_request, id_token_hash
        ):
            state_from_cookie = self._cookie_service.get_cookie(state_from_request)
            if state_from_request != state_from_cookie:
                # Error if state doesn't match.
                raise LtiMessageValidationException("State not found")

        return self

    def validate_jwt_format(self) -> "MessageLaunch":
        """
        Validate that the JWT included in the message launch is of the correct format.
        """
        id_token = self._get_id_token()
        jwt_parts = id_token.split(".")

        if len(jwt_parts) != 3:
            # Invalid number of parts in JWT.
            raise LtiMessageValidationException(
                "Invalid id_token, JWT must contain 3 parts"
            )

        try:
            # Decode JWT headers.
            header = self.urlsafe_b64decode(jwt_parts[0])
            self._jwt["header"] = json.loads(header)

            # Decode JWT body.
            body = self.urlsafe_b64decode(jwt_parts[1])
            self._jwt["body"] = json.loads(body)
        except Exception as e:
            raise LtiMessageValidationException(
                "Invalid JWT format, can't be decoded"
            ) from e

        return self

    def validate_nonce(self) -> "MessageLaunch":
        """
        Validate the launch's ``nonce`` parameter, using the session service.

        See https://openid.net/specs/openid-connect-core-1_0.html#IDToken.
        """
        nonce = self._get_jwt_body().get("nonce")
        if not nonce:
            raise LtiMessageValidationException('The "nonce" field is empty.')

        res = self._session_service.check_nonce(nonce)
        if not res:
            raise LtiInvalidNonceException("Invalid Nonce.")

        return self

    def validate_registration(self) -> "MessageLaunch":
        """
        Validate that the launch corresponds to a known platform registration.
        """
        iss = self.get_iss()
        jwt_body = self._get_jwt_body()
        client_id = self.get_client_id()

        # Mypy doesn't support higher kinded types yet so it thinks that all
        # generic attrs have type `Any`. See issue:
        # https://github.com/python/mypy/issues/8228
        config: ToolConfAbstract[REQ] = self._tool_config
        req: REQ = self._request

        # Find registration
        if config.check_iss_has_one_client(iss):
            self._registration = config.find_registration(
                iss, action=Action.MESSAGE_LAUNCH, request=req, jwt_body=jwt_body
            )
        else:
            self._registration = config.find_registration_by_params(
                iss,
                client_id,
                action=Action.MESSAGE_LAUNCH,
                request=req,
                jwt_body=jwt_body,
            )

        if not self._registration:
            raise LtiMessageValidationException("Registration not found.")

        # Check client id
        if client_id != self._registration.get_client_id():
            raise LtiMessageValidationException(
                "Client id not registered for this issuer"
            )

        return self

    def validate_jwt_signature(self) -> "MessageLaunch":
        """
        Validate thw signature of the JWT.
        """
        id_token = self._get_id_token()

        # Fetch public key object
        public_key, key_alg = self.get_public_key()

        try:
            jwt.decode(
                id_token,
                public_key,
                algorithms=[key_alg],
                options=self._jwt_verify_options,
            )
        except jwt.InvalidTokenError as e:
            raise LtiMessageValidationException(
                f"Can't decode id_token: {str(e)}"
            ) from e

        return self

    def validate_deployment(self) -> "MessageLaunch":
        """
        Check that the given ``deployment_id`` is valid, using the tool config.
        """
        iss = self.get_iss()
        client_id = self.get_client_id()
        deployment_id = self._get_deployment_id()
        tool_config: ToolConfAbstract = self._tool_config

        # Find deployment.
        if tool_config.check_iss_has_one_client(iss):
            deployment = tool_config.find_deployment(iss, deployment_id)
        else:
            deployment = tool_config.find_deployment_by_params(
                iss, deployment_id, client_id
            )
        if not deployment:
            raise LtiMessageValidationException(
                f'The deployment ID "{deployment_id}" is not recognised.'
            )

        return self

    def validate_message(self) -> "MessageLaunch":
        """
        Perform validation specific to the message type.

        See :py:func:`pylti1p3.message_validators.get_validators`.
        """
        jwt_body = self._get_jwt_body()
        message_type = jwt_body.get(
            "https://purl.imsglobal.org/spec/lti/claim/message_type", None
        )
        if not message_type:
            raise LtiMessageValidationException("Invalid message type")

        validators = get_validators()
        validated = False
        for validator in validators:
            if validator.can_validate(jwt_body):
                if validated:
                    raise LtiMessageValidationException("Validator conflict")
                validated = True
                res = validator.validate(jwt_body)
                if not res:
                    raise LtiMessageValidationException("Message validation failed")

        if not validated:
            raise LtiMessageValidationException("Unrecognized message type")

        return self

    def set_launch_data_storage(
        self, data_storage: LaunchDataStorage[t.Any]
    ) -> "MessageLaunch":
        """
        Set the launch data storage handler for this launch.

        If there is a session ID cookie, it's added to the ``LaunchDataStorage``.
        """
        data_storage.set_request(self._request)
        session_cookie_name = data_storage.get_session_cookie_name()
        if session_cookie_name:
            session_id = self._cookie_service.get_cookie(session_cookie_name)
            if session_id:
                data_storage.set_session_id(session_id)
            else:
                raise LtiException(f"Missing cookie {session_cookie_name}")
        self._session_service.set_data_storage(data_storage)
        return self

    def set_launch_data_lifetime(self, time_sec: int) -> "MessageLaunch":
        """
        Change the expiration time of keys in the session service.
        """
        self._session_service.set_launch_data_lifetime(time_sec)
        return self

    def save_launch_data(self) -> "MessageLaunch":
        """
        Save the launch data using the session service's cache. Called at the end of validation.
        """
        state_from_request = self._get_request_param("state")
        id_token_hash = self._get_id_token_hash()

        self._session_service.save_launch_data(self._launch_id, self._jwt["body"])
        self._session_service.set_state_valid(state_from_request, id_token_hash)
        return self

    def get_params_from_login(self):
        """
        Get the OIDC login parameters from the session service.
        """
        state = self._get_request_param("state")
        return self._session_service.get_state_params(state)

    def check_jwt_body_is_empty(self) -> bool:
        """
        Check that the JWT body is not empty.
        """
        # TODO - this doesn't seem to be used. Remove?
        jwt_body = self._get_jwt_body()
        return not jwt_body

    def check_staff_access(self) -> bool:
        """
        Does the user have a staff role?
        """
        jwt_body = self._get_jwt_body()
        return StaffRole(jwt_body).check()

    def check_student_access(self) -> bool:
        """
        Does the user have a student role?
        """
        jwt_body = self._get_jwt_body()
        return StudentRole(jwt_body).check()

    def check_teacher_access(self) -> bool:
        """
        Does the student have a teacher role?
        """
        jwt_body = self._get_jwt_body()
        return TeacherRole(jwt_body).check()

    def check_teaching_assistant_access(self) -> bool:
        """
        Does the user have a teaching assistant role?
        """
        jwt_body = self._get_jwt_body()
        return TeachingAssistantRole(jwt_body).check()

    def check_designer_access(self) -> bool:
        """
        Does the user have a designer role?
        """
        jwt_body = self._get_jwt_body()
        return DesignerRole(jwt_body).check()

    def check_observer_access(self) -> bool:
        """
        Does the user have an observer role?
        """
        jwt_body = self._get_jwt_body()
        return ObserverRole(jwt_body).check()

    def check_transient(self) -> bool:
        """
        Does the user have a transient role?
        """
        jwt_body = self._get_jwt_body()
        return TransientRole(jwt_body).check()
