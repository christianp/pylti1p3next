import typing_extensions as te


#: An enum describing action steps in the launch flow.
class Action:
    OIDC_LOGIN: te.Final = "oidc_login"
    MESSAGE_LAUNCH: te.Final = "message_launch"
