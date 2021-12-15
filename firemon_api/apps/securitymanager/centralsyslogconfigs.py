"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import json
import logging

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record, JsonField
from firemon_api.core.utils import _build_dict
from firemon_api.core.query import Request, url_param_builder

log = logging.getLogger(__name__)


class CentralSyslogConfig(Record):
    """Central Syslog Config Record

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "centralsyslogconfig"
    _is_domain_url = True

    def __init__(self, config, app):
        super().__init__(config, app)


class CentralSyslogConfigs(Endpoint):
    """Central Syslog Configs Endpoint

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "centralsyslogconfig"
    _is_domain_url = True

    def __init__(self, api, app, record=CentralSyslogConfig):
        super().__init__(api, app, record=CentralSyslogConfig)

    def filter(self, *args, **kwargs):
        csc_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [csc for csc in csc_all if kwargs.items() <= dict(csc).items()]

    def count(self):
        return len(self.all())
