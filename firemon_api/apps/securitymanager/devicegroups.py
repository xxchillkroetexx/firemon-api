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

from .access_path import NetworkAccessPath
from .devices import Devices, Device

log = logging.getLogger(__name__)


class DeviceGroup(Record):
    """Device Group Record

    Parameters:
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
        """assign a device by id to device group

        Parameters:
            id (int): Device id

        Returns:
            bool
        """
        key = f"device/{id}"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        req.post()

    def unassign(self, id: int):
        """unassign a device by id from device group

        Parameters:
            id (int): Device id

        Returns:
            bool
        """
        key = f"device/{id}"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        req.delete()

    def devices(self) -> list[Device]:
        """Get all devices assigned to device group

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

    def apa(
        self,
        *,
        starting_node_id: int,
        source_ip: str,
        dest_ip: str,
        protocol: int,
        source_port: int = None,
        dest_port: int = None,
        icmp_type: int = None,
        icmp_code: int = None,
        applications: list[str] = [],
        applicationsMatchingStrategy: str = "NONE",
        profiles: list[str] = [],
        profilesMatchingStrategy: str = "ANY",
        url_matchers: list[str] = [],
        urlMatchersMatchingStrategy: str = "ANY",
        users: list[str] = [],
        usersMatchingStrategy: str = "NONE",
        accept: bool = None,
        recommend: bool = None,
    ) -> NetworkAccessPath:
        """Perform an Network Access Path Analysis query

        Parameters:
            starting_node_id (int): Starting Network Segment Node ID (see NetworkSegmentNode)
            source_ip (str): ipv4/6 address ex: '192.168.202.95'
            dest_ip (str): ipv4/6 address ex: '192.168.203.66'
            protocol (int): for all practical purposes it is only 1 (icmp), 6 (tcp), 17 (udp), 58 (icmpv6)

        Keyword Arguments:
            source_port (int): source port
            dest_port (int): destination port. required if the protocol has ports
            icmp_type (int): apparently not required
            icmp_code (int): apparently not required
            applications (list[str]): Applications L7
            applicationsMatchingStrategy (str): ???
            profiles (list[str]): Profiles L7
            profilesMatchingStrategy (str): ???
            url_matchers (list[str]): URL Matcher L7
            urlMatchersMatchingStrategy (str): ???
            users (list[str]): Users L7
            usersMatchingStrategy (str): ???
            accept (bool): Rule Rec
            recommend (bool): Rule Rec

        Return:
            AccessPath: as always AccessPath().dump() gets you the dictionary. But the AccessPath object gets some parsed data. `events` as a list, `packet_result` as a dictionary.
        """
        json = {
            "startingNodeId": starting_node_id,
            "testIpPacket": {
                "sourceIp": source_ip,
                "destinationIp": dest_ip,
                "protocol": protocol,
            },
        }
        if isinstance(source_port, int):
            json["testIpPacket"]["sourcePort"] = source_port
        if isinstance(dest_port, int):
            json["testIpPacket"]["port"] = dest_port
        if isinstance(icmp_type, int):
            json["testIpPacket"]["icmpType"] = icmp_type
        if isinstance(icmp_code, int):
            json["testIpPacket"]["icmpCode"] = icmp_code
        if isinstance(applications, list):
            json["testIpPacket"]["applications"] = applications
        if isinstance(applicationsMatchingStrategy, str):
            json["testIpPacket"][
                "applicationsMatchingStrategy"
            ] = applicationsMatchingStrategy
        if isinstance(profiles, list):
            json["testIpPacket"]["profiles"] = profiles
        if isinstance(profilesMatchingStrategy, str):
            json["testIpPacket"]["profilesMatchingStrategy"] = profilesMatchingStrategy

        if isinstance(url_matchers, list):
            json["testIpPacket"]["urlMatchers"] = url_matchers
        if isinstance(urlMatchersMatchingStrategy, str):
            json["testIpPacket"][
                "urlMatchersMatchingStrategy"
            ] = urlMatchersMatchingStrategy
        if isinstance(users, list):
            json["testIpPacket"]["users"] = users
        if isinstance(usersMatchingStrategy, str):
            json["testIpPacket"]["usersMatchingStrategy"] = usersMatchingStrategy
        if isinstance(accept, bool):
            json["testIpPacket"]["accept"] = accept
        if isinstance(recommend, bool):
            json["testIpPacket"]["recommend"] = recommend

        key = "apa"

        req = Request(
            base=self._url,
            key=key,
            headers={
                "Content-Type": "application/json;",
                "accept": "application/json;",
            },
            session=self._session,
        )
        return NetworkAccessPath(req.put(json=json), self, self.id, apa_request=json)

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

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
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

        Parameters:
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
