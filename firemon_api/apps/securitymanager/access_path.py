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

# Local packages
from firemon_api.core.response import Record
from firemon_api.core.query import Request

log = logging.getLogger(__name__)


class AccessPathEvent(Record):
    """AccessPathEvent"""

    ep_name = "apa"
    _domain_url = True

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

    ep_name = "apa"
    _domain_url = True

    def __init__(self, config, app, device_id=None):
        self._device_id = device_id
        super().__init__(config, app)

        self.events = []
        self.packet_result = {}
        self._parse_apa()

    def _url_create(self):
        """ General self.url create """
        url = f"{self.ep_url}/device/{self._device_id}/{self.__class__.ep_name}"
        return url

    def _parse_apa(self):
        se = self._config["startingEvent"]
        self._parse_event(se)
        if self.events:
            levent = self.events[-1]
            if getattr(levent, "ipPacketResult", None):
                self.packet_result = getattr(levent, "ipPacketResult").dump()

    def _parse_event(self, event):
        ne = None
        if event.get("nextEvents"):
            if len(event["nextEvents"]) > 1:
                log.debug("multiple events")
            ne = event["nextEvents"][0]
            event.pop("nextEvents")
        self.events.append(AccessPathEvent(event, self, self.url))
        if ne:
            self._parse_event(ne)

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
