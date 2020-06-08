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
    """ Represents the Central Syslog Config

    Args:
        api (obj): FiremonAPI()
        endpoint (obj): Endpoint()
        config (dict): dictionary of things values from json
    """

    def __init__(self, api, endpoint, config):
        super().__init__(api, endpoint, config)
        self.url = '{ep}/{id}'.format(ep=self.endpoint.ep_url, 
                                      id=config['id'])

    def __repr__(self):
        return("<CentralSyslogConfig(id='{}, name='{}')>".format(
                                                self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))


class CentralSyslogConfigs(Endpoint):
    """ Represents the Central Syslog Configs
    
    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint
    """

    def __init__(self, api, app, name, record=CentralSyslogConfig):
        super().__init__(api, app, name, record=CentralSyslogConfig)
        self.ep_url = "{url}/{ep}".format(url=app.domain_url,
                                          ep=name)

    def filter(self, *args, **kwargs):
        # Create to grab all and do some lookup
        pass

    def count(self):
        return len(self.all())

