# Standard packages
import logging

# Local packages
from .errors import ControlPanelError
from firemon_api.core.endpoint import EndpointCpl
from firemon_api.core.response import Record
from firemon_api.core.query import Request

log = logging.getLogger(__name__)


class Value(Record):
    pass


class Database(EndpointCpl):

    ep_name = "database"

    def __init__(self, api, app):
        super().__init__(api, app)

    def standby_all(self):
        """Get list of standby db"""
        key = "standby/"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req

    def standby_get(self, fqdn: str):
        """Get info about standby db

        Args:
            fqdn (str): db fqdn
        """
        key = f"standby/{fqdn}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req

    def standby_create(self, fqdn: str):
        """Create standby db

        Args:
            fqdn (str): db fqdn
        """
        key = f"standby/"
        data = {"fqdn": fqdn}
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).post(data=data)
        return req

    def standby_delete(self, fqdn: str):
        """Delete standby db

        Args:
            fqdn (str): db fqdn
        """
        key = f"standby/{fqdn}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).delete()
        return req

    def shutdown(self):
        """shutdown db"""
        key = f"shutdown"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).post()
        return req
