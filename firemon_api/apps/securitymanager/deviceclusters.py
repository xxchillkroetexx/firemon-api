# Standard packages
import logging

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request

from .devices import Device

log = logging.getLogger(__name__)


class DeviceCluster(Record):
    """Device Cluster Record

    Parameters:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:

        >>> cluster = fm.sm.deviceclusters.get(name="my cluster")
        >>> cluster.devices()
        [<Device(F5-V13-1)>, <Device(NS-5XP)>, <Device(cp-r8030-fw-d1-2)>]
    """

    _ep_name = "cluster"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def devices(self) -> list[Device]:
        """Get all devices assigned to cluster

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


class DeviceClusters(Endpoint):
    """Represents the Device Clusters

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
        record (obj): default `Record` object

    Examples:

        >>> cluster = fm.sm.deviceclusters.get(name="my cluster")
        >>> fm.sm.deviceclusters.all()
    """

    ep_name = "cluster"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=DeviceCluster):
        super().__init__(api, app, record=record)
