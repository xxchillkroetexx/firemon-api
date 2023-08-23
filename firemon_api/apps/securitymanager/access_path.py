"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import logging
import copy

from typing import Optional, Never

# Local packages
from firemon_api.apps import SecurityManager
from firemon_api.core.response import Record
from firemon_api.core.query import Request, RequestResponse

log = logging.getLogger(__name__)


class AccessPathEvent(Record):
    """AccessPathEvent"""

    _ep_name = "apa"
    _is_domain_url = True

    def __init__(self, config, app, url):
        self._url = url
        super().__init__(config, app)

    def _url_create(self):
        return self._url

    def save(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported.")

    def update(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported.")

    def delete(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported.")


class AccessPath(Record):
    """AccessPath"""

    _ep_name = "apa"
    _is_domain_url = True

    def __init__(
        self,
        config: dict,
        app: SecurityManager,
        device_id: Optional[int] = None,
        apa_request={},
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

    def save(self, arg: Never) -> None:
        raise NotImplementedError("Writes are not supported.")

    def update(self, arg: Never) -> None:
        raise NotImplementedError("Writes are not supported.")

    def delete(self, arg: Never) -> None:
        raise NotImplementedError("Writes are not supported.")

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
