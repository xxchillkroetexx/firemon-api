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
from urllib.parse import urlencode, quote

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder, RequestError

from .devices import Device

log = logging.getLogger(__name__)


class DeviceCluster(Record):
    """Device Cluster Record

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:
        >>> cluster = fm.sm.deviceclusters.get(name="my cluster")
        >>> cluster.devices()
        [<Device(F5-V13-1)>, <Device(NS-5XP)>, <Device(cp-r8030-fw-d1-2)>]
    """

    _ep_name = "cluster"
    _is_domain_url = True

    def __init__(self, config, app):
        super().__init__(config, app)

    def devices(self):
        """Get all devices assigned to cluster"""
        key = "device"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return [Device(config, self._app) for config in req.get()]


class DeviceClusters(Endpoint):
    """Represents the Device Clusters

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object

    Examples:
        >>> cluster = fm.sm.deviceclusters.get(name="my cluster")
        >>> fm.sm.deviceclusters.all()
    """

    ep_name = "cluster"
    _is_domain_url = True

    def __init__(self, api, app, record=DeviceCluster):
        super().__init__(api, app, record=DeviceCluster)
