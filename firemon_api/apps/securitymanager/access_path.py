# Standard packages
import logging
import copy

from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.response import BaseRecord
from firemon_api.core.query import Request, RequestResponse

log = logging.getLogger(__name__)


class AccessPathEvent(BaseRecord):
    """Access Path Event"""

    _ep_name = "apa"
    _is_domain_url = True

    def __init__(self, config: dict, app: App, url: str):
        self._url = url
        super().__init__(config, app)

    def _url_create(self):
        return self._url


class AccessPath(BaseRecord):
    """AccessPath"""

    _ep_name = "apa"
    _is_domain_url = True

    def __init__(
        self,
        config: dict,
        app: App,
        device_id: Optional[int] = None,
        apa_request: dict = {},
    ):
        self._device_id = device_id
        self._apa_request = apa_request
        super().__init__(config, app)
        self._ep_url = f"{self._domain_url}/device/{self._device_id}/apa"
        self._url = self._ep_url

        self.paths = []
        self._parse_apa()

    def _url_create(self) -> str:
        """General self._url create"""
        url = f"{self._ep_url}"
        return url

    def _parse_apa(self) -> None:
        """Attempt to parse the JSON blob into a list (paths) of of events so they are
        a bit easier to work with.

        """
        se = self._config["startingEvent"].copy()
        path = {
            "branch": se["id"],
            "branch_parent": None,
            "event_ordinal": 0,
            "packet_result": {},
            "events": [],
        }
        self._parse_event(se, path)

    def _parse_event(self, event: dict, path: dict) -> None:
        path["events"].append(AccessPathEvent(event, self, self._url))

        if event.get("nextEvents"):
            if len(event["nextEvents"]) > 1:
                for i, evnt in enumerate(event["nextEvents"][::-1]):
                    # This seems like a bug in APA needing to process in
                    # reverse to mimic policy order match.
                    # branch_path = path.copy()  # can this be done with shallow copy?
                    branch_path = copy.deepcopy(path)
                    if i > 0:
                        branch_path["branch_parent"] = event["id"]
                        branch_path["branch"] = evnt["id"]
                        branch_path["event_ordinal"] = len(branch_path["events"])
                    self._parse_event(evnt, branch_path)
            else:
                self._parse_event(event["nextEvents"][0], path)
        else:
            path["packet_result"] = event.get("ipPacketResult", {})
            self.paths.append(path)

    def get_graphml(self) -> RequestResponse:
        req = Request(
            base=self._url,
            headers={
                "Content-Type": "application/json;",
                "accept": "application/xml;",
            },
            session=self._session,
        )
        return req.put(json=self._apa_request)

    def __str__(self):
        return str("AccessPath")

    def __repr__(self):
        if self._device_id:
            s = f"<{self.__class__.__name__}(dev:{self._device_id})>"
        else:
            s = f"<{self.__class__.__name__}>"
        return s
