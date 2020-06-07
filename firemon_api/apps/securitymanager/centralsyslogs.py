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
from firemon_api.core.response import Record
from firemon_api.core.utils import _build_dict
from firemon_api.core.query import Request, url_param_builder

log = logging.getLogger(__name__)


class CentralSyslog(Record):
    """ Represents the Central Syslog

    Args:
        cs (obj): CentralSyslogs()
    """

    def __init__(self, api, endpoint, config):
        super().__init__(api, endpoint, config)
        self.id = config['id']
        self.url = '{ep}/{id}'.format(ep=self.endpoint.ep_url, 
                                      id=self.id)  # CS URL

    def delete(self):
        """ Delete Central Syslog device

        Examples:
            >>> cs = fm.sm.centralsyslog.get(13)
            >>> cs
            detroit
            >>> cs.delete()
            True
        """
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('DELETE ' + url)
        response = self.session.delete(self.url)
        if response.status_code == 204:
            return True
        else:
            raise FiremonError("ERROR deleting central-syslog! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def update(self):
        """ Todo: send update config to CS """
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

    def filter(self, arg):
        """Filter devices based on search parameters.
        central-syslog only has a single search. :shrug:

        Args:
            arg (str): filter/search

        Available Filters:
            name (you read that correct, name is the only one. STUPID)

        Return:
            list: List of CentralSyslog(objects)
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.centralsyslog.filter('mia')
            [miami, miami-2]
        """

        url = '{ep}?&search={arg}'.format(ep=self.ep_url,
                                                        arg=arg)
        req = Request(
            base=url,
            session=self.api.session,
        )

        ret = [self._response_loader(i) for i in req.get()]
        return ret

    def create(self, *args, **kwargs):
        """ Create a new Central Syslog

        Args:
            args (dict/optional): a dictionary of all the config settings for a CS
            kwargs (optional): name and settings for a CS. minimum need 'name', 'ip'

        Return:
            int: id for newly created CS

        Examples:
            Create by dictionary
            >>> fm.sm.centralsyslogs.create({'name': 'miami', 'ip': '10.2.2.2'})
            11

            Create by keyword
            >>> fm.sm.centralsyslogs.create(name='new york', ip='10.2.2.3')
            12
        """
        try:
            config = args[0]
            config['domainId'] = int(self.sm.api.domainId)  # API is dumb to auto-fill
        except IndexError:
            config = None
        if not config:
            config = kwargs
            config['domainId'] = self.sm.api.domainId # API is dumb to auto-fill
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('POST ' + url)
        response = self.session.post(self.url, json=config)
        if response.status_code == 200:
            return json.loads(response.content)['id']
        else:
            raise FiremonError("ERROR creating central-syslog! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))



