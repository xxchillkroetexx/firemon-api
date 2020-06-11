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
        api (obj): FiremonAPI()
        app (obj): App()
        config (dict): dictionary of things values from json
    """

    ep_name = 'centralsyslogconfig'
    domain = True

    def __init__(self, api, app, config):
        super().__init__(api, app, config)

    def __repr__(self):
        return("<CentralSyslogConfig(id='{}, name='{}')>".format(
                                                self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))


class CentralSyslogConfigs(Endpoint):
    """Central Syslog Configs Endpoint
    
    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = 'centralsyslogconfig'
    domain = True

    def __init__(self, api, app, record=CentralSyslogConfig):
        super().__init__(api, app, record=CentralSyslogConfig)

    def filter(self, *args, **kwargs):
        csc_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [csc for csc in csc_all if kwargs.items() <= dict(csc).items()]

    def count(self):
        return len(self.all())

