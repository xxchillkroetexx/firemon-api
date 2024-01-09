# Standard packages
import logging

# Local packages
from firemon_api.core.errors import ControlPanelError
from firemon_api.core.endpoint import EndpointCpl
from firemon_api.core.query import Request

log = logging.getLogger(__name__)


class Config(EndpointCpl):
    ep_name = "config"

    def __init__(self, api, app):
        super().__init__(api, app)
        self.options()

    def apply(self):
        key = "apply"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).post()
        return req

    def categories(self):
        key = "categories"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req

    def options(self, config: dict = None):
        if not config:
            config = {"show_advanced": True, "show_deprecated": True}

        key = "options"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).put(json=config)
        return req

    def state(self):
        """config state"""
        key = "state"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req

    def get(self, category: str):
        """Get config values
        Parameters:
            category (str): whatever
        """
        key = f"values/{category}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req

    def update(self, category: str, config: dict):
        """Update config values
        Parameters:
            category (str): whatever
            config (dict): update data
        """
        key = f"values/{category}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).put(json=config)
        return req

    def schema(self, category: str):
        """Schema config values. Show how to make your dict for whatever
        Parameters:
            category (str): whatever
        """
        key = f"schema/{category}"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req
