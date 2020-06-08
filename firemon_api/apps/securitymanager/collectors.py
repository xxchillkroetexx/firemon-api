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

        # add attributes to Record() for more info
        #self.devices = Devices(self.dcs.sm, collectorId=self.id)

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
        """Get a list of devices assigned to Collector
        """
        url = "{ep}/device".format(ep=self.url)
        req = Request(
            base=url,
            session=self.api.session,
        )
        return [Device(self.api, 
                Devices(self.api, self.endpoint.app, 'device'
                record=Device), config) for config in req.get()]

class Collectors(Endpoint):
    """ Represents the Data Collectors

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint
    """

    def __init__(self, api, app, name, record=Collector):
        super().__init__(api, app, name, record=Collector)


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

    def member_assign(self, cid):
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

    def member_remove(self, cid):
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

    def device_assign(self, id):
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
        return("<CollectorGroup(id='{}', name='{}')>".format(
                                                        self.id,
                                                        self.name))

    def __str__(self):
        return("{}".format(self.name))


class CollectorGroups(Endpoint):
    """ Represents the Data Collector Groups

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint
    """

    def __init__(self, api, app, name, record=CollectorGroup):
        super().__init__(api, app, name, record=CollectorGroup)
