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
from firemon_api.errors import (
    AuthenticationError, FiremonError, LicenseError,
    DeviceError, DevicePackError, VersionError
)
from firemon_api.core.response import Record

log = logging.getLogger(__name__)


class CentralSyslogs(object):
    """ Represents the Central Syslogs

    Args:
        sm (obj): SecurityManager
    """

    def __init__(self, sm):
        self.sm = sm
        #self.domainId = sm.domainId
        #self.sm_url = sm.sm_url  # sec mgr url
        self.domain_url = sm.domain_url  # Domain URL
        self.url = self.domain_url + '/central-syslog'  # CSs URL
        self.session = sm.session

    def all(self):
        """ Get all central syslog servers

        Return:
            list: List of CentralSyslog(object)

        Examples:
            >>> cs = fm.sm.centralsyslog.all()
            [cs_test2, cs_test2, cs_test1, miami, miami, new york, detroit]
        """
        url = self.url + '?pageSize=100'  # Note: I'm not bothering with anything beyond 100. That's crazy
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                return [CentralSyslog(self, cs) for cs in resp['results']]
            else:
                return None
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def get(self, *args, **kwargs):
        """ Get single device

        Args:
            *args (int): (optional) Device id to retrieve
            **kwargs (str): (optional) see filter() for available filters

        Examples:
            Get by ID
            >>> fm.sm.centralsyslogs.get(12)
            new york

            Get by partial name. Case insensative.
            >>> fm.sm.centralsyslogs.get(name='detro')
            detroit
        """
        try:
            id = args[0]
            url = self.url + '/{id}'.format(id=str(id))
            self.session.headers.update({'Content-Type': 'application/json'})
            response = self.session.get(url)
            if response.status_code == 200:
                return CentralSyslog(self, response.json())
            else:
                raise DeviceError("ERROR retrieving device! HTTP code: {}"
                                   " Server response: {}".format(
                                   response.status_code, response.text))
        except IndexError:
            id = None
        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                            "get() returned more than one result. "
                            "Check that the kwarg(s) passed are valid for this "
                            "or use filter() or all() instead."
                        )
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        """ Filter devices based on search parameters

        Args:
            **kwargs (str): filter parameters

        Available Filters:
            name (you read that correct, name is the only one. STUPID)

        Return:
            list: List of CentralSyslog(objects)
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.centralsyslog.filter(name='mia')
            [miami, miami-2]

            Note: did not implement multiple pages. Figured 100 CS is extreme.
        """
        if not kwargs:
            raise ValueError('filter() must be passed kwargs. ')
        url = self.url + '?pageSize=100&search={filters}'.format(
                                filters=next(iter(kwargs.values())))  # just takeing the first kwarg value meh
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                return[CentralSyslog(self, cs) for cs in resp['results']]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

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
        response = self.session.post(self.url, json=config)
        if response.status_code == 200:
            return json.loads(response.content)['id']
        else:
            raise FiremonError("ERROR creating central-syslog! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def __repr__(self):
        return("<CentralSyslogs(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class CentralSyslog(Record):
    """ Represents the Central Syslog

    Args:
        cs (obj): CentralSyslogs()
    """

    def __init__(self, cs, config):
        super().__init__(cs, config)
        self.cs = cs
        self.url = cs.url + '/{id}'.format(id=self.id)  # CS URL

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
