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
import uuid

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request, url_param_builder
from .devices import Devices, Device

log = logging.getLogger(__name__)


class Collector(Record):
    """ Represents the Data Collector

    Args:
        api (obj): FiremonAPI()
        endpoint (obj): Endpoint()
        config (dict): dictionary of things values from json
    """

    def __init__(self, api, endpoint, config):
        super().__init__(api, endpoint, config)
        self.url = '{ep}/{id}'.format(ep=self.endpoint.ep_url, 
                                      id=config['id'])

        self._Devices = Devices(self.api, self.endpoint.app, 'device')

    def status(self):
        """Get status of Collector"""
        url = '{ep}/status/{id}'.format(ep=self.endpoint.ep_url,
                                    id=self.id)
        req = Request(
            base=url,
            session=self.api.session,
        )
        return req.get()

    def devices(self):
        """Get all devices assigned to collector"""
        req = Request(
            base="{}/device".format(self.url),
            session=self.api.session,
        )

        return [Device(self.api, self._Devices, config) for config in req.get()]

    def __repr__(self):
        if len(str(self.id)) > 10:
            id = '{}...'.format(self.id[0:9])
        else:
            id = self.id
        if len(self.name) > 10:
            name = '{}...'.format(self.name[0:9])
        else:
            name = self.name
        return("<Collector(id='{}', name='{}')>".format(id, name))

    def __str__(self):
        return("{}".format(self.name))

class Collectors(Endpoint):
    """ Represents the Data Collectors

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        record (obj): default `Record` object
    """

    def __init__(self, api, app, name, record=Collector):
        super().__init__(api, app, name, record=Collector)

    def filter(self, *args, **kwargs):
        """Filter devices based on search parameters.
        collector only has a single search. :shrug:
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

class CollectorGroup(Record):
    """ Represents the Collector Group

    Args:
        api (obj): FiremonAPI()
        endpoint (obj): Endpoint()
        config (dict): dictionary of things values from json
    """

    def __init__(self, api, endpoint, config):
        super().__init__(api, endpoint, config)
        self.url = '{ep}/{id}'.format(ep=self.endpoint.ep_url, 
                                      id=config['id'])

    def member_list(self):
        """ Get all data collector objects

        Return:
            list: List of Collector(object)
        """
        return [Collectors(self.sm).get(mem['id'])
                for mem in self._config['members']]

    def member_get(self, cid):
        """
        Args:
            cid (int): Collector ID
        """
        return Collectors(self.sm).get(cid)

    def member_set(self, cid):
        """
        Args:
            cid (int): Collector ID
        """
        url = self.url + '/member/{collectorId}'.format(collectorId=cid)
        log.debug('PUT {}'.format(self.url))
        response = self.session.put(url)
        if response.status_code == 200:
            self._reload()
            return True
        else:
            return False

    def member_unset(self, cid):
        """
        Args:
            cid (int): Collector ID
        """
        config = self._config.copy()
        for member in config['members']:
            if member['id'] == cid:
                log.debug('removing member: {}'.format(member))
                config['members'].remove(member)

        config['id'] = self._config['id']  # make sure this is set appropriately
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('PUT {}'.format(self.url))
        response = self.session.put(self.url, json=config)
        if response.status_code == 200:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR removing memember! HTTP code: {} "
                            "Content {}".format(
                                            response.status_code,
                                            response.text))

    def device_set(self, id):
        """ Assign a Device
        Args:
            id (int): Device id
        """
        url = self.url + '/assigned/{deviceId}'.format(deviceId=id)
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('PUT {}'.format(self.url))
        response = self.session.put(url)
        if response.status_code == 200:
            return True
        else:
            raise DeviceError("ERROR assigning Device! HTTP code: {} "
                            "Content {}".format(
                                            response.status_code,
                                            response.text))

    def __repr__(self):
        if len(str(self.id)) > 10:
            id = '{}...'.format(self.id[0:9])
        else:
            id = self.id
        if len(self.name) > 10:
            name = '{}...'.format(self.name[0:9])
        else:
            name = self.name
        return("<CollectorGroup(id='{}', name='{}')>".format(id, name))

    def __str__(self):
        return("{}".format(self.name))


class CollectorGroups(Endpoint):
    """ Represents the Data Collector Groups

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        record (obj): default `Record` object
    """

    def __init__(self, api, app, name, record=CollectorGroup):
        super().__init__(api, app, name, record=CollectorGroup)

    def filter(self, *args, **kwargs):
        """Filter devices based on search parameters.
        collectorgroup only has a single search. :shrug:
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

    def count(self):
        return len(self.all())