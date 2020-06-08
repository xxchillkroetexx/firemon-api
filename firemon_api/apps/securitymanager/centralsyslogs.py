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
    """ Represents the Central Syslog

    Args:
        api (obj): FiremonAPI()
        endpoint (obj): Endpoint()
        config (dict): dictionary of things values from json
    """
    centralSyslogConfig = CentralSyslogConfig

    def __init__(self, api, endpoint, config):
        super().__init__(api, endpoint, config)
        self.url = '{ep}/{id}'.format(ep=self.endpoint.ep_url, 
                                      id=config['id'])

        # not needed for `serialize` update using ep function
        self.no_no_keys = ['centralSyslogConfig']

    def device_set(self, id: int):
        """Set a device to this Central Syslog

        Args:
            id (int): device id to assign
        
        Returns:
            (bool): True if assigned
        """
        url = '{ep}/devices/{id}'.format(ep=self.url, id=id)
        req = Request(
            base=url,
            session=self.api.session,
        )
        return req.post(None)

    def device_unset(self, id: int):
        """Unset a device to this Central Syslog

        Args:
            id (int): device id to assign
        
        Returns:
            (bool): True if assigned
        """
        url = '{ep}/devices/{id}'.format(ep=self.url, id=id)
        req = Request(
            base=url,
            session=self.api.session,
        )
        return req.delete()

    def csc_set(self, id: int):
        """Set a Central Syslog Config to this CS

        Args:
            id (int): Central Syslog Config id to assign
        
        Returns:
            (bool): True if assigned
        """
        url = '{ep}/config/{id}'.format(ep=self.url, id=id)
        req = Request(
            base=url,
            session=self.api.session,
        )
        return req.put(None)

    def devices(self):
        # todo: return all devices assigned to this CS
        pass

    def __repr__(self):
        return("<CentralSyslog(id='{}', name='{}')>".format(self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))


class CentralSyslogs(Endpoint):
    """ Represents the Central Syslogs
    
    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint
    """

    def __init__(self, api, app, name, record=CentralSyslog):
        super().__init__(api, app, name, record=CentralSyslog)
        self.ep_url = "{url}/{ep}".format(url=app.domain_url,
                                          ep=name)

    def filter(self, *args, **kwargs):
        """Filter devices based on search parameters.
        central-syslog only has a single search. :shrug:

        Args:
            arg (str): filter/search

        Available Filters:
            name (you read that correct, name is the only one. STUPID)

        Return:
            list: List of CentralSyslog(objects)

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.centralsyslog.filter('mia')
            [miami, miami-2]
        """

        srch = None
        if args:
            srch = args[0]
        elif kwargs:
            # Just get the value of first kwarg.
            srch = kwargs[next(iter(kwargs))]
        if not srch:
            log.debug('No filter provided. Here is an empty list.')
            return []
        url = '{ep}?&search={srch}'.format(ep=self.ep_url,
                                                srch=srch)
        
        req = Request(
            base=url,
            session=self.api.session,
        )

        ret = [self._response_loader(i) for i in req.get()]
        return ret

