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
from firemon_api.errors import (
    AuthenticationError, FiremonError, LicenseError,
    DeviceError, DevicePackError, VersionError
)
from firemon_api.core.response import Record
from .devices import Devices, Device

log = logging.getLogger(__name__)


class Collectors(object):
    """ Represents the Data Collectors

    Args:
        sm (obj): SecurityManager object
    """

    def __init__(self, sm):
        self.sm = sm
        self.url = sm.sm_url + '/collector'  # Collector URL
        self.session = sm.session

    def all(self):
        """ Get all data collector servers

        Return:
            list: List of Collector(object)

        Examples:
            >>> collectors = fm.sm.collectors.all()
            [..., ..., ..., ..., ]
        """
        total = 0
        page = 0
        count = 0
        url = self.url + '?page={page}&pageSize=100'.format(page=page)
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                results = resp['results']
                total = resp['total']
                count = resp['count']
                while total > count:
                    page += 1
                    url = self.url + '?page={page}&pageSize=100'.format(
                                                                    page=page)
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
            if resp['results']:
                return [Collector(self, col) for col in resp['results']]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                                                        response.status_code,
                                                        response.text))

    def get(self, *args, **kwargs):
        """ Get single collector

        Args:
            *args (int): (optional) Collector id to retrieve
            **kwargs (str): (optional) see filter() for available filters

        Examples:
            Get by ID
            >>> fm.sm.collectors.get(2)
            ...

        """
        try:
            id = args[0]
            url = self.url + '/{id}'.format(id=str(id))
            self.session.headers.update({'Content-Type': 'application/json'})
            response = self.session.get(url)
            if response.status_code == 200:
                return Collector(self, response.json())
            else:
                raise DeviceError("ERROR retrieving device! HTTP code: {}"
                                   " Server response: {}".format(
                                                        response.status_code,
                                                        response.text))
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
            name (you read that correct, name is the only one)

        Return:
            list: List of Collector(objects)
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.collectors.filter(name='dc')
            [..., ]

            Note: did not implement multiple pages. Figured 100 collectors is extreme.
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
                return[Collector(self, col) for col in resp['results']]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    #def create(self, *args, **kwargs):
    #    """ Create a new Collector
    #
    #    Args:
    #        args (dict): a dictionary of all the config settings for a Collector
    #
    #    Return:
    #        int: id for newly created Collector
    #
    #    Examples:
    #
    #    Create by dictionary
    #    >>> fm.sm.c...
    #    """
    #    try:
    #        config = args[0]
    #        config['domainId'] = int(self.domainId)  # API is dumb to auto-fill
    #    except IndexError:
    #        config = None
    #    if not config:
    #        config = kwargs
    #        config['domainId'] = self.domainId # API is dumb to auto-fill
    #    self.session.headers.update({'Content-Type': 'application/json'})
    #    response = self.session.post(self.url, json=config)
    #    if response.status_code == 200:
    #        return json.loads(response.content)['id']
    #    else:
    #        raise FiremonError("ERROR creating collector! HTTP code: {}"
    #                           " Server response: {}".format(
    #                           response.status_code, response.text))

    def __repr__(self):
        return("<Collectors(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class Collector(Record):
    """ Represents the Data Collector

    Args:
        dcs (obj): Collectors() object

    Attributes:
        devices
    """

    def __init__(self, dcs, config):
        super().__init__(dcs, config)
        self.dcs = dcs
        self.url = dcs.url + '/{id}'.format(id=self.id)  # DC URL
        self.session = dcs.session
        self.sm = dcs.sm

        # add attributes to Record() for more info
        self.devices = Devices(self.dcs.sm, collectorId=self.id)

    def delete(self):
        """ Delete Data Collector device

        Raises:
            firemon_api.errors.FiremonError: if not status code 204

        Examples:
            >>> dc = fm.sm.collectors.get(name='wasp.lab.firemon.com')
            >>> dc.delete()
        """
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.delete(self.url)
        if response.status_code == 204:
            return True
        else:
            raise FiremonError("ERROR deleting data collector! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def update(self):
        """ Todo: send update config to Data Collector """
        pass

    def device_assign(self, id, retrieve: bool=False):
        """ Assign a device to Data Collector

        Args:
            id (int): Device Id

        Kwargs:
            retrieve (bool): Perform manual retrieval after successful change
        """
        url = self.url + '/device/{deviceId}?manualRetrieval={retrieve}'.format(
                                            deviceId=id,
                                            retrieve=str(retrieve))
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug(url)
        response = self.session.post(url)
        if response.status_code == 204:
            return True
        else:
            raise FiremonError("ERROR assigning device to DC! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def device_remove(self, id):
        """ Delete a device from a Data Collector

        Args:
            id (int): Device Id
        """
        url = self.url + '/device/{deviceId}'.format(deviceId=id)
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug(url)
        response = self.session.delete(url)
        if response.status_code == 204:
            return True
        else:
            raise FiremonError("ERROR assigning device to DC! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def __repr__(self):
        return("<Collector(id='{}', name='{}')>".format(self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))


class CollectorGroups(object):
    """ Represents the Data Collector Groups

    Args:
        sm (obj): SecurityManager object
    """

    def __init__(self, sm):
        self.sm = sm
        self.url = sm.sm_url + '/collector/group'  # Collector Groups URL
        self.session = sm.session

    def all(self):
        """ Get all data collector groups

        Return:
            list: List of CollectorGroup(object)

        Examples:
            >>> cg = fm.sm.collectorgroups.all()
            [..., ..., ..., ..., ]
        """
        url = self.url + '?pageSize=100'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                return [CollectorGroup(self, cg) for cg in resp['results']]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def get(self, *args, **kwargs):
        """ Get single collector group

        Args:
            *args (uuid): (optional) CollectorGroup id to retrieve
            **kwargs (str): (optional) see filter() for available filters

        Examples:
            Get by ID
            >>> fm.sm.collectorgroups.get(2)
            ...

        """
        try:
            id = args[0]
            url = self.url + '/{id}'.format(id=str(id))
            self.session.headers.update({'Content-Type': 'application/json'})
            response = self.session.get(url)
            if response.status_code == 200:
                return CollectorGroup(self, response.json())
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
        """ Filter collector groups based on search parameters

        Args:
            **kwargs (str): filter parameters

        Available Filters:
            ?

        Return:
            list: List of CollectorGroup(objects)
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.collector.filter(name='dc')
            [..., ]

            Note: did not implement multiple pages.
                  Figured 100 collectors is extreme.
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
                return[CollectorGroup(self, cg) for cg in resp['results']]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def create(self, *args, **kwargs):
        """ Create a new CollectorGroup

        Args:
            args (dict): a dictionary of all the config settings
                         for a CollectorGroup

        Return:
            CollectorGroup()

        Examples:

        Create by dictionary
        >>> fm.sm.c...
        """
    pass

    def __repr__(self):
        return("<CollectorGroups(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class CollectorGroup(Record):
    """ Represents the Collector Group

    Args:
        dcgs (obj): CollectorGroups() object

    Attributes:
        * devices
    """

    def __init__(self, dcgs, config):
        super().__init__(dcgs, config)
        self.dcgs = dcgs
        self.url = dcgs.url + '/{id}'.format(id=self.id)  # DC URL
        self.session = dcgs.session
        self.sm = dcgs.sm

        # add attributes to Record() for more info
        self.devices = Devices(self.dcgs.sm, collectorGroupId=self.id)

    def _reload(self):
        """ Todo: Get configuration info upon change """
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(self.url)
        if response.status_code == 200:
            config = response.json()
            self._config = config.copy()
            self.__init__(self.dcgs, self._config)
        else:
            raise FiremonError('Error! unable to reload CollectorGroup')

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

    def member_add(self, cid):
        """
        Args:
            cid (int): Collector ID
        """
        url = self.url + '/member/{collectorId}'.format(cid)
        log.debug(url)
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
                config['members'].remove(member)

        config['id'] = self._config['id']  # make sure this is set appropriately
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('PUT ' + self.url)
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
        log.debug('PUT ' + url)
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


class CGMembers(object):
    """ Represents the Data Collectors

    Args:
        sm (obj): SecurityManager object
        id (str): uuid for Collector Group
        members (list): a list dictionary objects
    """

    def __init__(self, sm, id, members):
        self.sm = sm
        self.id = id
        self.members = members
        self.url = sm.sm_url + '/collector/group'  # Collector Groups URL
        self.session = sm.session

    def all(self):
        """ Get all data collector objects

        Return:
            list: List of Collector(object)
        """
        return [Collectors(self.sm).get(mem['id']) for mem in self.members]

    def get(self, cid):
        """
        Args:
            cid (int): Collector ID
        """
        return Collectors(self.sm).get(cid)

    def add(self, cid):
        """
        Args:
            cid (int): Collector ID
        """
        url = self.url + '/{id}/member/{collectorId}'.format(self.id, cid)
        log.debug(url)
        response = self.session.put(url)
        if response.status_code == 200:
            return True
        else:
            return False

    def remove(self, cid):
        """
        Args:
            cid (int): Collector ID
        """
        url = self.url + '/{id}'.format(self)
        log.debug(url)
        response = self.session.put(url)
        if response.status_code == 200:
            return True
        else:
            return False


class CGDevices(object):
    pass
