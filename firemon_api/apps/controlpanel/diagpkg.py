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


class DiagPkg(EndpointCpl):
    ep_name = "diagpkg"

    def __init__(self, api, app):
        super().__init__(api, app)

    def all(self):
        """Get list of diag packages"""
        req = Request(
            base=self.url,
            session=self.session,
            trailing_slash=True,
        ).get()
        return req

    def get(self, name: str):
        """Get diag package

        Args:
            name (str): package name
        """
        key = f"{name}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req

    def create(self, ticket: str, upload=False):
        """Create diag package

        Args:
            ticket (str): ticket number

        Kwargs:
            upload (bool): default False
        """
        data = {"ticket": ticket, "upload": upload}
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        req = Request(
            base=self.url,
            headers=headers,
            session=self.session,
            trailing_slash=True,
        ).post(data=data)

        return req

    def delete(self, name: str):
        """Delete package

        Args:
            name (str): package name
        """
        key = f"{name}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).delete()
        return req
