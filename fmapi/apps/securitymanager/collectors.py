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

# Local packages
from fmapi.errors import (
    AuthenticationError, FiremonError, LicenseError,
    DeviceError, DevicePackError, VersionError
)
from fmapi.core.response import Record


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
            >>> collectors = fm.sm.collector.all()
            [..., ..., ..., ..., ]
        """
        url = self.url + '?pageSize=100'  # Note: I'm not bothering with anything beyond 100. That's crazy
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                return [DataCollector(self, col) for col in resp['results']]
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
            >>> fm.sm.collectors.get(2)
            ...

        """
        try:
            id = args[0]
            url = self.url + '/{id}'.format(id=str(id))
            self.session.headers.update({'Content-Type': 'application/json'})
            response = self.session.get(url)
            if response.status_code == 200:
                return DataCollector(self, response.json())
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
            name (you read that correct, name is the only one)

        Return:
            list: List of DataCollector(objects)
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.collector.filter(name='dc')
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
                return[DataCollector(self, col) for col in resp['results']]
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


class DataCollector(Record):
    """ Represents the Data Collector

    Args:
        dcs (obj): Collectors() object
    """

    def __init__(self, dcs, config):
        super().__init__(dcs, config)
        self.dcs = dcs
        self.url = dcs.url + '/{id}'.format(id=self.id)  # DC URL
        self.session = dcs.session

    def delete(self):
        """ Delete Data Collector device

        Raises:
            fmapi.errors.FiremonError: if not status code 204

        Examples:
            >>> dc = fm.sm.collectors.get(name='wasp.lab.firemon.com')
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

    def device_list(self):
        """ Get all devices assigned to DataCollector

        Return:
            list: List of Device(object)

        Raises:
            fmapi.errors.DeviceError: if not status code 200

        Examples:
            >>> devices = dc.device_list()
        """
        total = 0
        page = 0
        count = 0
        url = self.url + '/device?page={page}&pageSize=100'.format(page=page)
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
                    url = self.url + '/device?page={page}&pageSize=100'.format(page=page)
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                return [Device(self, dev) for dev in results]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def device_assign(self):
        """ Todo: assign a device to DC """
        pass

    def device_remove(self):
        """ Todo: remove a device from a DC """
        pass

    def __repr__(self):
        return("<DataCollector(id='{}', name='{}')>".format(self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))
