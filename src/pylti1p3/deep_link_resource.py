import typing as t
from .lineitem import LineItem


class DeepLinkResource:
    """
        A resource to return in the deep link flow.

        See https://www.imsglobal.org/spec/lti-dl/v2p0/#lti-resource-link.
    """

    _type: str = "ltiResourceLink" #: The type of the resource. See `https://www.imsglobal.org/spec/lti-dl/v2p0/#content-item-types`__.
    _title: t.Optional[str] = None #: The title of the resource.
    _url: t.Optional[str] = None #: The URL of the resource.
    _lineitem: t.Optional[LineItem] = None #: A lineItem object associated with this resource.
    _custom_params: t.Mapping[str, str] = {} #: Any custom parameters to include in any launch for this resource.
    _target: str = "iframe" #: not used???
    _icon_url: t.Optional[str] = None #: The URL of an icon for this resource.

    def get_type(self):
        return self._type

    def set_type(self, value: str) -> "DeepLinkResource":
        self._type = value
        return self

    def get_title(self) -> t.Optional[str]:
        return self._title

    def set_title(self, value: str) -> "DeepLinkResource":
        self._title = value
        return self

    def get_url(self) -> t.Optional[str]:
        return self._url

    def set_url(self, value: str) -> "DeepLinkResource":
        self._url = value
        return self

    def get_lineitem(self) -> t.Optional[LineItem]:
        return self._lineitem

    def set_lineitem(self, value: LineItem) -> "DeepLinkResource":
        self._lineitem = value
        return self

    def get_custom_params(self) -> t.Mapping[str, str]:
        return self._custom_params

    def set_custom_params(self, value: t.Mapping[str, str]) -> "DeepLinkResource":
        self._custom_params = value
        return self

    def get_target(self) -> str:
        return self._target

    def set_target(self, value: str) -> "DeepLinkResource":
        self._target = value
        return self

    def get_icon_url(self) -> t.Optional[str]:
        return self._icon_url

    def set_icon_url(self, value: str) -> "DeepLinkResource":
        self._icon_url = value
        return self

    def to_dict(self) -> t.Dict[str, object]:
        """
            Produce a dictionary representing this resource, to use in the deep link response.
        """
        res: t.Dict[str, object] = {
            "type": self._type,
            "title": self._title,
            "url": self._url,
        }
        if self._lineitem:
            line_item: t.Dict[str, object] = {
                "scoreMaximum": self._lineitem.get_score_maximum(),
            }

            label = self._lineitem.get_label()
            if label:
                line_item["label"] = label

            resource_id = self._lineitem.get_resource_id()
            if resource_id:
                line_item["resourceId"] = resource_id

            tag = self._lineitem.get_tag()
            if tag:
                line_item["tag"] = tag

            submission_review = self._lineitem.get_submission_review()
            if submission_review:
                line_item["submissionReview"] = submission_review

            res["lineItem"] = line_item

        if self._icon_url:
            res["icon"] = {"url": self._icon_url}

        if self._custom_params:
            res["custom"] = self._custom_params

        return res
