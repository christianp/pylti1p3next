import json
import typing as t
import typing_extensions as te
from .exception import LineItemException


"""
    Settings for the submission review message.

    See https://www.imsglobal.org/spec/lti-ags/v2p0/#submission-review-message
"""
TSubmissionReview = te.TypedDict(
    "TSubmissionReview",
    {
        # Required data
        "reviewableStatus": list,
        # Optional data
        "label": str,
        "url": str,
        "custom": t.Dict[str, str],
    },
    total=False,
)

"""
    Data for a line item.
"""
TLineItem = te.TypedDict(
    "TLineItem",
    {
        "id": str,
        "scoreMaximum": int,
        "label": str,
        "resourceId": str,
        "tag": str,
        "resourceLinkId": str,
        "startDateTime": str,
        "endDateTime": str,
        "submissionReview": TSubmissionReview,
    },
    total=False,
)


class LineItem:
    """
        An Assignments and Grades Service line item: a gradable activity belonging to a context.
    """

    _id: t.Optional[str] = None
    _score_maximum: t.Optional[float] = None
    _label: t.Optional[str] = None
    _resource_id: t.Optional[str] = None
    _resource_link_id: t.Optional[str] = None
    _tag: t.Optional[str] = None
    _start_date_time: t.Optional[str] = None
    _end_date_time: t.Optional[str] = None
    _submission_review: t.Optional[TSubmissionReview] = None

    def __init__(self, lineitem: t.Optional[TLineItem] = None):
        if not lineitem:
            lineitem = {}
        self._id = lineitem.get("id")
        self._score_maximum = lineitem.get("scoreMaximum")
        self._label = lineitem.get("label")
        self._resource_id = lineitem.get("resourceId")
        self._resource_link_id = lineitem.get("resourceLinkId")
        self._tag = lineitem.get("tag")
        self._start_date_time = lineitem.get("startDateTime")
        self._end_date_time = lineitem.get("endDateTime")
        self._submission_review = lineitem.get("submissionReview")

    def get_id(self) -> t.Optional[str]:
        #: Get the line item's ID.
        return self._id

    def set_id(self, value: str) -> "LineItem":
        #: Set the line item's ID.
        self._id = value
        return self

    def get_label(self) -> t.Optional[str]:
        """
        Get the line item's label.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#label
        """
        return self._label

    def set_label(self, value: str) -> "LineItem":
        """
        Set the line item's label.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#label
        """
        self._label = value
        return self

    def get_score_maximum(self) -> t.Optional[float]:
        """
        Get the maximum possible score for the line item, or ``None`` if not set.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#scoremaximum
        """
        return self._score_maximum

    def set_score_maximum(self, value: float) -> "LineItem":
        """
        Set the maximum possible score for the line item.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#scoremaximum
        """
        # TODO: validating scores is done here and in pylti1p3.grade, so don't repeat the code.
        if not isinstance(value, (int, float)):
            raise LineItemException(
                "Invalid scoreMaximum value: score must be integer or float"
            )
        if value <= 0:
            raise LineItemException(
                "Invalid scoreMaximum value: score must be non null value, strictly greater than 0"
            )

        self._score_maximum = value
        return self

    def get_resource_id(self) -> t.Optional[str]:
        """
        Get the ID of the resource this line item is associated with.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#tool-resource-identifier-resourceid
        """
        return self._resource_id

    def set_resource_id(self, value: str) -> "LineItem":
        """
        Set the ID of the resource this line item is associated with.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#tool-resource-identifier-resourceid
        """
        self._resource_id = value
        return self

    def get_resource_link_id(self) -> t.Optional[str]:
        """
        Get the ID of the resource link this lineitem is associated with.

        https://www.imsglobal.org/spec/lti-ags/v2p0#resourcelinkid-and-binding-a-line-item-to-a-resource-link
        """
        return self._resource_link_id

    def set_resource_link_id(self, value: str) -> "LineItem":
        """
        Set the ID of the resource link this lineitem is associated with.

        https://www.imsglobal.org/spec/lti-ags/v2p0#resourcelinkid-and-binding-a-line-item-to-a-resource-link
        """
        self._resource_link_id = value
        return self

    def get_tag(self) -> t.Optional[str]:
        """
        Get the line item's tag.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#tag
        """
        return self._tag

    def set_tag(self, value: str) -> "LineItem":
        """
        Set the line item's tag.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#tag
        """
        self._tag = value
        return self

    def get_start_date_time(self) -> t.Optional[str]:
        """
        Get the line item's ``startDateTime`` property.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#startdatetime
        """
        return self._start_date_time

    def set_start_date_time(self, value: str) -> "LineItem":
        """
        Set the line item's ``startDateTime`` property.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#startdatetime
        """
        self._start_date_time = value
        return self

    def get_end_date_time(self) -> t.Optional[str]:
        """
        Get the line item's ``endDateTime`` property.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#enddatetime
        """
        return self._end_date_time

    def set_end_date_time(self, value: str) -> "LineItem":
        """
        Set the line item's ``endDateTime`` property.

        https://www.imsglobal.org/spec/lti-ags/v2p0/#enddatetime
        """
        self._end_date_time = value
        return self

    def get_submission_review(self) -> t.Optional[TSubmissionReview]:
        return self._submission_review

    def set_submission_review(
        self,
        reviewable_status: t.List,
        label: t.Optional[str] = None,
        url: t.Optional[str] = None,
        custom: t.Optional[t.Dict[str, str]] = None,
    ) -> "LineItem":
        """
            Set the submission review settings for this line item.
        """
        if not isinstance(reviewable_status, list):
            raise LineItemException('Invalid "reviewable_status" argument')

        self._submission_review: TSubmissionReview = {
            "reviewableStatus": reviewable_status
        }
        if label:
            self._submission_review["label"] = label
        if url:
            self._submission_review["url"] = url
        if custom:
            self._submission_review["custom"] = custom

        return self

    def get_value(self) -> str:
        """
            A JSON representation of this line item, to send to the AGS.
        """
        data = {
            "id": self._id if self._id else None,
            "scoreMaximum": self._score_maximum,
            "label": self._label,
            "resourceId": self._resource_id,
            "resourceLinkId": self._resource_link_id,
            "tag": self._tag,
            "startDateTime": self._start_date_time,
            "endDateTime": self._end_date_time,
            "submissionReview": self._submission_review,
        }
        return json.dumps({k: v for k, v in data.items() if v})
