# Standard packages
# import json
import logging

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request, RequestResponse

from firemon_api.apps.structure.collector import UsageObjects, RuleUsages, Usage
from .devices import Device

log = logging.getLogger(__name__)


class Collector(Record):
    """Represents the Data Collector

    Parameters:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "collector"

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def status(self) -> RequestResponse:
        """Get status of Collector

        Returns:
            dict
        """
        key = f"status/{self.id}"
        req = Request(
            base=self._ep_url,
            key=key,
            session=self._session,
        )
        return req.get()

    def devices(self) -> list[Device]:
        """Get all devices assigned to collector

        Returns:
            list[Device]
        """
        key = "device"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return [Device(config, self._app) for config in req.get()]


class Collectors(Endpoint):
    """Represents the Data Collectors

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
        record (obj): default `Record` object
    """

    ep_name = "collector"

    def __init__(self, api: FiremonAPI, app: App, record=Collector):
        super().__init__(api, app, record=record)

    def _make_filters(self, values):
        # Only a 'search' for a single value. Take all key-values
        # and use the first key's value for search query
        filters = {"search": values[next(iter(values))]}
        return filters

    def save_usage(
        self, config: Usage, async_aggregation: bool = True
    ) -> RequestResponse:
        """Save usage

        Parameters:
            config (Usage): dictionary of usage data.

        Return:
            bool
        """
        filters = {"asyncAggregation": async_aggregation}
        key = "usage"
        req = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        )

        return req.post(json=config)


class CollectorGroup(Record):
    """Represents the Collector Group

    Parameters:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "collector/group"

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def member_set(self, cid: int) -> RequestResponse:
        """Assign a Collector to Group.

        note: no changes if device is already assigned.

        Parameters:
            cid (int): Collector ID
        """
        key = f"member/{cid}"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return req.put()

    # def member_unset(self, cid):
    # Need to get this working to make set useful
    #    pass

    def device_set(self, id: int) -> RequestResponse:
        """Assign a Device

        Notes:
            No changes if device is already assigned. How to unassign?

        Parameters:
            id (int): Device id

        Returns:
            bool
        """
        key = f"member/{id}"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return req.put()

    def assigned(self) -> RequestResponse:
        """Get assigned devices

        Returns:
            dict
        """
        key = f"assigned"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return req.get()


class CollectorGroups(Endpoint):
    """Represents the Data Collector Groups

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
        record (obj): default `Record` object
    """

    ep_name = "collector/group"

    def __init__(self, api: FiremonAPI, app: App, record=CollectorGroup):
        super().__init__(api, app, record=record)

    def _make_filters(self, values):
        # Only a 'search' for a single value. Take all key-values
        # and use the first key's value for search query
        filters = {"search": values[next(iter(values))]}
        return filters

    def count(self):
        return len(self.all())
