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
from .centralsyslogconfigs import CentralSyslogConfig

log = logging.getLogger(__name__)


class CentralSyslog(Record):
    """Central Syslog Record

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    ep_name = 'central-syslog'
    _domain_url = True    
    centralSyslogConfig = CentralSyslogConfig

    def __init__(self, config, app):
        super().__init__(config, app)

        # not needed for `serialize` update using ep function
        self._no_no_keys = ['centralSyslogConfig']

    def device_set(self, id: int):
        """Set a device to this Central Syslog

        Args:
            id (int): device id to assign
        
        Returns:
            (bool): True if assigned
        """
        key = 'devices/{id}'.format(id=id)
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.post()

    def device_unset(self, id: int):
        """Unset a device to this Central Syslog

        Args:
            id (int): device id to assign
        
        Returns:
            (bool): True if assigned
        """
        key = 'devices/{id}'.format(id=id)
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.delete()

    def csc_set(self, id: int):
        """Set a Central Syslog Config to this CS

        Args:
            id (int): Central Syslog Config id to assign
        
        Returns:
            (bool): True if assigned
        """
        key = 'config/{id}'.format(id=id)
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.put()

    def devices(self):
        # todo: return all devices assigned to this CS
        pass

    def __repr__(self):
        return("<CentralSyslog(id='{}', name='{}')>".format(self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))


class CentralSyslogs(Endpoint):
    """Central Syslogs Endpoint
    
    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = 'central-syslog'
    _domain_url = True

    def __init__(self, api, app, record=CentralSyslog):
        super().__init__(api, app, record=CentralSyslog)

    def _make_filters(self, values):
        # Only a 'search' for a single value. Take all key-values
        # and use the first key's value for search query
        filters = {'search': values[next(iter(values))]}
        return filters
