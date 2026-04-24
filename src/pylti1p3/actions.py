import typing_extensions as te


class Action:
    """ An enum describing action steps in the launch flow. """
    OIDC_LOGIN: te.Final = "oidc_login" #: The OIDC login.
    MESSAGE_LAUNCH: te.Final = "message_launch" #: The final launch message.
