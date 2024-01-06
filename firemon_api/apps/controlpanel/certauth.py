# Standard packages
import logging

# Local packages
from firemon_api.core.errors import ControlPanelError
from firemon_api.core.endpoint import EndpointCpl
from firemon_api.core.response import Record
from firemon_api.core.query import Request

log = logging.getLogger(__name__)


class Value(Record):
    pass


class CertAuth(EndpointCpl):
    ep_name = "ca"

    def __init__(self, api, app):
        super().__init__(api, app)

    def root_crt(self):
        key = "root.crt"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req

    def chain(self, cert_type: str):
        """
        Args:
            cert_type (str): "host", "server", "database"
        """

        if not cert_type in ("host", "server", "database"):
            raise ControlPanelError(
                "cert_type must be either 'host', 'server', 'database'"
            )

        key = f"chain/{cert_type}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req

    def sign(self, cert_type: str):
        """
        Args:
            cert_type (str): "host", "server", "database"
        """

        if not cert_type in ("host", "server", "database"):
            raise ControlPanelError(
                "cert_type must be either 'host', 'server', 'database'"
            )

        key = f"sign/{cert_type}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).post()
        return req
