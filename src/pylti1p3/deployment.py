import typing as t


class Deployment:
    """
        Represents a deployment of the tool.
    """

    _deployment_id: t.Optional[str] = None

    def get_deployment_id(self) -> t.Optional[str]:
        """ Get the deployment's ID. """
        return self._deployment_id

    def set_deployment_id(self, deployment_id: str) -> "Deployment":
        """ Set the deployment's ID and return the deployment object. """
        self._deployment_id = deployment_id
        return self
