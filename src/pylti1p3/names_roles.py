import typing as t
import typing_extensions as te
from .utils import add_param_to_url
from .service_connector import ServiceConnector

#: Settings for the names and roles provisioning service, from the launch message.
TNamesAndRolesData = te.TypedDict(
    "TNamesAndRolesData",
    {
        "context_memberships_url": str,
    },
    total=False,
)

#: Data to do with a member of the course.
TMember = te.TypedDict(
    "TMember",
    {
        "name": str,
        "status": te.Literal["Active", "Inactive", "Deleted"],
        "picture": str,
        "given_name": str,
        "family_name": str,
        "middle_name": str,
        "email": str,
        "user_id": str,
        "lis_person_sourcedid": str,
        "roles": t.List[str],
        "message": t.Union[t.List[t.Dict[str, object]], t.Dict[str, object]],
        "lti11_legacy_user_id": t.Optional[str],
    },
    total=False,
)


class NamesRolesProvisioningService:
    """
    Handles interaction with the Names and Roles Provisioning Service.

    Don't create this directly; use :py:func:`pylti1p3.message_launch.MessageLaunch.get_nrps()` to create an instance from a launch message.

    See the spec at https://www.imsglobal.org/spec/lti-nrps/v2p0.
    """
    _service_connector: ServiceConnector
    _service_data: TNamesAndRolesData

    def __init__(
        self, service_connector: ServiceConnector, service_data: TNamesAndRolesData
    ):
        self._service_connector = service_connector
        self._service_data = service_data

    def get_nrps_data(self, members_url: t.Optional[str] = None):
        """
        Request a page of member data from the platform.
        """
        if not members_url:
            members_url = self._service_data["context_memberships_url"]

        data = self._service_connector.make_service_request(
            [
                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
            ],
            members_url,
            accept="application/vnd.ims.lti-nrps.v2.membershipcontainer+json",
        )
        return data

    def get_members_page(
        self, members_url: t.Optional[str] = None
    ) -> t.Tuple[t.List[TMember], t.Optional[str]]:
        """
        Get one page of member data.

        :return: tuple in format: (list with users, next page URL)
        """
        data = self.get_nrps_data(members_url=members_url)
        data_body = t.cast(t.Any, data.get("body", {}))
        return data_body.get("members", []), data["next_page_url"]

    def get_members(self, resource_link_id: t.Optional[str] = None) -> t.List[TMember]:
        """
        Get all members of the context from the platform, as a list.

        If the resource link ID is given, only members with access to that resource link are returned, if the platform supports it.
        See https://www.imsglobal.org/spec/lti-nrps/v2p0#resource-link-membership-service.
        """
        members_res_lst: t.List[TMember] = []
        members_url: t.Optional[str] = self._service_data["context_memberships_url"]

        if members_url and resource_link_id:
            members_url = add_param_to_url(members_url, "rlid", resource_link_id)

        while members_url:
            members, members_url = self.get_members_page(members_url)
            members_res_lst.extend(members)

        return members_res_lst

    def get_context(self):
        """
        Get data about the context from the NRPS: at least its ID, and usually also a title and label.

        You normally already have this information.

        See https://www.imsglobal.org/spec/lti-nrps/v2p0#sharing-of-personal-data.

        :return: dict
        """
        data = self.get_nrps_data()
        data_body = t.cast(t.Any, data.get("body", {}))
        return data_body.get("context", {})
