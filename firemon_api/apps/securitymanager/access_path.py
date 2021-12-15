"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import copy
import logging

# Local packages
from firemon_api.core.response import Record
from firemon_api.core.query import Request

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

    def save(self):
        raise NotImplementedError("Writes are not supported.")

    def update(self):
        raise NotImplementedError("Writes are not supported.")

    def delete(self):
        raise NotImplementedError("Writes are not supported.")


class AccessPath(Record):
    """AccessPath"""

    _ep_name = "apa"
    _is_domain_url = True

    def __init__(self, config, app, device_id=None):
        self._device_id = device_id
        super().__init__(config, app)

        self.paths = []
        self._parse_apa()

    def _url_create(self):
        """ General self._url create """
        url = f"{self._ep_url}/device/{self._device_id}/{self.__class__._ep_name}"
        return url

    def _parse_apa(self):
        se = self._config["startingEvent"].copy()
        path = {
            "branch": se["id"],
            "packet_result": {},
            "events": [],
        }
        self._parse_event(se, path)

    def _parse_event(self, event, path):

        path["events"].append(AccessPathEvent(event, self, self._url))
        _ = copy.deepcopy(path)

        if event.get("nextEvents"):
            for i, v in enumerate(event["nextEvents"]):
                if i == 0:
                    # primary path
                    self._parse_event(v, _)
                else:
                    # branch
                    _["branch"] = v["id"]
                    self._parse_event(v, _)
        else:
            # assume last event in path
            _["packet_result"] = event.get("ipPacketResult", {})
            self.paths.append(_)

    def save(self):
        raise NotImplementedError("Writes are not supported.")

    def update(self):
        raise NotImplementedError("Writes are not supported.")

    def delete(self):
        raise NotImplementedError("Writes are not supported.")

    def __str__(self):
        return str("AccessPath")

    def __repr__(self):
        if self._device_id:
            s = f"<{self.__class__.__name__}(dev:{self._device_id})>"
        else:
            s = f"<{self.__class__.__name__}>"
        return s
