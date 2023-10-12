"""
(c) 2023 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import logging
from typing import Optional, Literal

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request
from firemon_api.apps.structure import RuleRecRequirement

from .devices import Devices, Device
from .rulerec import RuleRecommendation

log = logging.getLogger(__name__)


class DeviceGroup(Record):
    """Device Group Record

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:
        >>> dg = fm.sm.devicegroups.get("my group")
        >>> dg.devices()
        [<Device(F5-V13-1)>, <Device(NS-5XP)>, <Device(cp-r8030-fw-d1-2)>]
    """

    _ep_name = "devicegroup"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def assign(self, id: int):
        """assign a device by id to device group"""
        key = f"device/{id}"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        req.post()

    def unassign(self, id: int):
        """unassign a device by id from device group"""
        key = f"device/{id}"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        req.delete()

    def devices(self) -> list[Device]:
        """Get all devices assigned to device group"""
        key = "device"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return [Device(config, self._app) for config in req.get()]

    def rule_rec_startingdevices(
        self,
        requirement: RuleRecRequirement,
        license_category: Optional[
            Literal[
                "LOG_SERVERS",
                "ROUTERS",
                "OPERATING_SYSTEMS",
                "FIREWALLS",
                "FIREWALL_MANAGER_MODULES",
                "EDGE_DEVICES",
                "GENERIC_DEVICES",
                "TRAFFIC_MANAGER_MODULES",
                "UNKNOWN",
                "SALES_ONLY_SMLO_HA",
                "SALES_ONLY_SMSO_HA",
                "SALES_ONLY_SMM_HA",
                "POLICY_PLANNER",
                "RISK",
                "POLICY_OPTIMIZER",
                "INSIGHT",
                "GLOBAL_POLICY_CONTROLLER",
                "AUTOMATION",
                "LICENSE_NOT_REQUIRED",
            ]
        ] = None,
    ) -> list[Device]:
        """Find devices in a Device Group that would have recommendable changes.
        Probably preferable to use `rule_rec_devices()`
        """
        key = "rulerec/startingdevices"
        filters = {}
        device_l = []
        if license_category:
            filters["licenseCategory"] = license_category
        resp = Request(
            base=self._url,
            key=key,
            filters=filters,
            session=self._session,
        ).put(json=requirement)

        devices = Devices(self._app.api, self._app)
        for d in resp:
            dev = devices.get(d["id"])
            device_l.append(dev)
        return device_l

    def rule_rec_devices(
        self,
        requirement: RuleRecRequirement,
        license_category: Optional[
            Literal[
                "LOG_SERVERS",
                "ROUTERS",
                "OPERATING_SYSTEMS",
                "FIREWALLS",
                "FIREWALL_MANAGER_MODULES",
                "EDGE_DEVICES",
                "GENERIC_DEVICES",
                "TRAFFIC_MANAGER_MODULES",
                "UNKNOWN",
                "SALES_ONLY_SMLO_HA",
                "SALES_ONLY_SMSO_HA",
                "SALES_ONLY_SMM_HA",
                "POLICY_PLANNER",
                "RISK",
                "POLICY_OPTIMIZER",
                "INSIGHT",
                "GLOBAL_POLICY_CONTROLLER",
                "AUTOMATION",
                "LICENSE_NOT_REQUIRED",
            ]
        ] = None,
        strategy: Literal["NAME_PATTERN", "HITCOUNT", "REFERENCES", "NONE"] = "NONE",
        force_tiebreak: Optional[bool] = None,
        pattern: Optional[str] = None,
        include_error_recs: Optional[bool] = None,
    ) -> list[Device]:
        """Find devices in a Device Group that would have recommendable changes."""
        key = f"rulerec"
        filters = {}
        if license_category:
            filters["licenseCategory"] = license_category
        if strategy:
            filters["strategy"] = strategy
        if force_tiebreak:
            filters["forceTiebreak"] = force_tiebreak
        if pattern:
            filters["pattern"] = pattern
        if include_error_recs:
            filters["includeErrorRecs"] = include_error_recs
        device_l = []
        resp = Request(
            base=self._url,
            key=key,
            filters=filters,
            session=self._session,
        ).put(json=requirement)

        devices = Devices(self._app.api, self._app)
        for item in resp:
            for rec in item.get("recs", []):
                dev = devices.get(rec["device"]["id"])
                device_l.append(dev)
        return device_l


class DeviceGroups(Endpoint):
    """Represents the Device Groups

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object

    Examples:
        >>> cluster = fm.sm.devicegroups.get(name="my group")
        >>> fm.sm.devicegroups.all()
    """

    ep_name = "devicegroup"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=DeviceGroup):
        super().__init__(api, app, record=record)

    def _make_filters(self, values):
        # Only a 'search' for a single value. Take all key-values
        # and use the first key's value for search query
        filters = {"search": values[next(iter(values))]}
        return filters

    def get(self, *args, **kwargs) -> Optional[DeviceGroup]:
        """Get single DeviceGroup

        Args:
            *args (int/str): (optional) id or name to retrieve.
            **kwargs (str): (optional) see filter() for available filters

        Examples:
            Get by ID
            >>> fm.sm.devicegroupss.get(3)

            >>> fm.sm.devicegroups.get("my group")
            <DeviceGroup(my group)>
        """

        try:
            key = str(int(args[0]))
            req = Request(
                base=self.url,
                key=key,
                session=self.api.session,
            )
            return self._response_loader(req.get())
        except ValueError:
            # attempt to get by name
            key = f"name/{args[0]}"
            req = Request(
                base=self.url,
                key=key,
                session=self.api.session,
            )
            return self._response_loader(req.get())
        except IndexError:
            key = None

        if not key:
            if kwargs:
                filter_lookup = self.filter(**kwargs)
            else:
                filter_lookup = self.filter(*args)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result. "
                        "Check that the kwarg(s) passed are valid for this "
                        "endpoint or use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None
