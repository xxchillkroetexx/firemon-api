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


class CollectionConfigs(Endpoint):
    """ Represents the Collection Configs
    Filtering is terrible given the API.
    As a kludge I just ingest all collectionconfigs (like the device packs)
    and create get() and filter() functions to parse a dictionary.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        devicepack_id (int): Device Pack id
        device_id (int): Device id

    Examples:
        >>> cc = fm.sm.cc.get(46)
        >>> cc = fm.sm.cc.filter(
                activatedForDevicePack=True,
                devicePackArtifactId='juniper_srx')[0]
    """
    def __init__(self, 
                api, app, 
                name,
                devicepack_id: int=None, 
                device_id: int=None):
        super().__init__(api, app, name)
        # Use setter. Intended for use when CollectionConfigs() is called from Device()
        self._devicepack_id = devicepack_id
        self._device_id = device_id

        # dictionary of all the configs so we can search and filter
        self._collectionconfigs = {}

    def _get_all(self) -> dict:
        """ Get all configs and put them into a dict so we can search

        Return:
            dict: a dictionary
        """
        total = 0
        page = 0
        count = 0
        if self.devicepack_id:
            url = self.url + ('?devicePackId={devicepack_id}&page={page}&'
                'pageSize=100'.format(
                                devicepack_id=self.devicepack_id, page=page))
        else:
            url = self.url + '?page={page}&pageSize=100'.format(page=page)
        log.debug('GET {}'.format(self.url))
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
                    url = self.url + ('?sort=devicePack.vendor&page={page}&'
                                    'pageSize=100'.format(page=page))
                    log.debug('GET {}'.format(self.url))
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                self._collectionconfigs = _build_dict(results, 'id')
            else:
                self._collectionconfigs = {}
        else:
            raise FiremonError("ERROR retrieving Collection Configs!")

    def all(self):
        """ Get all collection configs

        Return:
            list: List of CollectionConfig(object)

        Examples:
            >>> configs = fm.sm.cc.all()
        """
        self._get_all()
        return [CollectionConfig(self, self._collectionconfigs[id])
                for id in self._collectionconfigs]

    def get(self, *args, **kwargs):
        """ Query and retrieve individual CollectionConfig

        Args:
            *args (int): The collectionconfig ID
            **kwargs: key value pairs in a collectionconfig dictionary

        Return:
            CollectionConfig(object): a single CollectionConfig(object)

        Examples:
            >>> fm.sm.cc.get(8)
            8
            >>> cc = fm.sm.cc.get(8)
            >>> type(cc)
            <class 'firemon_api.apps.securitymanager.CollectionConfig'>
            >>> cc = fm.sm.cc.get(name='Grape Ape')
            >>> cc
            46
        """
        #if not self._revisions:
        #    self._get_all()
        self._get_all()
        try:
            id = args[0]
            try:
                cc = self._collectionconfigs[id]
                return CollectionConfig(self, cc)
            except KeyError:
                raise FiremonError("ERROR retrieving collectionconfig. "
                                    "CC does not exist")
        except (KeyError, IndexError):
            id = None

        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError("get() returned more than one result."
                                    "Check the kwarg(s) passed are valid or"
                                    "use filter() or all() instead.")
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        """ Retrieve a filterd list of CollectionConfigs
        Note: review the

        Args:
            **kwargs: key value pairs in a collectionconfig dictionary

        Return:
            list: a list of CollectionConfig(object)

        Examples:
            >>> fm.sm.cc.filter(devicePackArtifactId='juniper_srx')
            [47, 21, 46]

            >>> fm.sm.cc.filter(activatedForDevicePack=True, devicepack_id=40)
            [21]

            >>> fm.sm.cc.filter(devicePackDeviceType='FIREWALL')
            [4, 24, 13, 8, 30, 31, 3, 5, ...]

            >>> fm.sm.cc.filter(activatedForDevicePack=True)
            [4, 36, 18, 38, 24, 13, 8, 30, ...]
        """
        #if not self._revisions:
        #    self._get_all()
        self._get_all()

        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [CollectionConfig(self, self._collectionconfigs[id]) for id in
                self._collectionconfigs if kwargs.items()
                <= self._collectionconfigs[id].items()]

    def create(self, dev_config: dict):
        """ WARNING! This is dangerous as you can overwrite 'default' configs
        by passing in the default's ID.

        Pass configuration information to create a new CollectionConfig.

        Args:
            dev_config (dict): a dictionary containing values for a collection

        Return:
            object: CollectionConfig object for your newly created config

        Examples:
            Duplicate an existing config
            >>> cc = fm.sm.cc.get(21)
            >>> config = dict(cc)
            >>> config.pop('index')
            >>> config['name'] = 'Conan the Collector'

            *IMPORTANT* If the following is not done you will overwrite an existing
            config, including defaults (or go ahead and create a system devoted only
            to Juniper collections)
            >>> config.pop('id')
            >>> fm.sm.cc.create(config)

            *DO NOT DO THIS*
            >>> for cc in fm.sm.cc.all():
            ...   config = dict(cc)
            ...   config['changePattern'] = 'shrug'
            ...   config['usagePattern'] = 'shrug'
            ...   config['name'] = 'defau1t'
            ...   config.pop('index')
            ...   fm.sm.cc.create(config)
            ...
        """
        assert(isinstance(dev_config, dict)), 'Configuration needs to be a dict'
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('POST {}'.format(self.url))
        response = self.session.post(self.url, json=dev_config)
        if response.status_code == 200:
            config = json.loads(response.content)
            return self.get(config['id'])
        else:
            raise DeviceError("ERROR creating Collection Config! HTTP code: {} "
                              "Server response: {}".format(
                                                    response.status_code,
                                                    response.text))

    def duplicate(self, id: int, name: str):
        """ Duplicate an existing Collection Config. Safer method than create.

        Args:
            id (int): The ID for an existing Collection Config
            name (str): The name for your new config

        Return:
            object: CollectionConfig of your newly created config
        """
        cc = self.get(id)
        config = cc._config.copy()
        no_no_keys = ['index',
            'id']
        for k in no_no_keys:
            config.pop(k)

        config['name'] = name
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('POST {}'.format(self.url))
        response = self.session.post(self.url, json=config)
        if response.status_code == 200:
            config = json.loads(response.content)
            return self.get(config['id'])
        else:
            raise FiremonError("ERROR creating Collection Config! HTTP code: {}"
                              " Server response: {}".format(
                              response.status_code, response.text))

    @property
    def devicepack_id(self):
        return self._devicepack_id

    @devicepack_id.setter
    def devicepack_id(self, id):
        self._devicepack_id = id

    @property
    def device_id(self):
        return self._device_id

    @device_id.setter
    def device_id(self, id):
        self._device_id = id


class CollectionConfig(Record):
    """ Represents a collection configuration in Firemon

    Args:
        ccs: CollectionConfigs() object
        config (dict): all the things

    Examples:
        Get a list of all Collection Configs
        >>> fm.sm.cc.all()
        [4, 36, 18, 38, 24, ...]

        Get a Collection Config by ID
        >>> cc = fm.sm.cc.get(47)
        >>> cc
        47
        >>> dict(cc)
        {'id': 47, 'name': 'Ape Grape', 'devicepack_id': 40, ...}

        Set a Device by ID to the Collection Config
        >>> cc.set_device(21)
        True
        If CC is already associated with a Device()
        >>> cc.set_device()
        True

        Set this CC as the default for associate Device Pack
        >>> cc.set_dp()
        True
    """
    def __init__(self, ccs, config):
        super().__init__(ccs, config)

        self.ccs = ccs
        self._device_id = ccs._device_id  # Should be 'None' unless coming through Device()
        self.url = ccs.url  # cc URL

    def _reload(self):
        url = self.url + '/{id}'.format(id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('GET {}'.format(self.url))
        response = self.session.get(url)
        if response.status_code == 200:
            config = response.json()
            self._config = config.copy()
            self.__init__(self.ccs, self._config)
        else:
            raise FiremonError('Error! unable to reload collection config')

    def set_dp(self) -> bool:
        """ Set CollectionConfig for Device Pack assignment. """
        url = self.url + '/devicepack/{devicepack_id}/assignment/{id}'.format(
                                            devicepack_id=self.devicepack_id,
                                            id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('PUT {}'.format(self.url))
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        return False

    def unset_dp(self) -> bool:
        """ Unset CollectionConfig for Device Pack assignment.
        Effectively sets back to 'default'
        """
        url = self.url + '/devicepack/{devicepack_id}/assignment'.format(
                                            devicepack_id=self.devicepack_id)
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('DELETE {}'.format(self.url))
        response = self.session.delete(url)
        if response.status_code == 204:
            self._reload()
            return True
        return False

    def set_device(self, *args) -> bool:
        """ Set CollectionConfig for a device by ID. If requested device IDs
        device pack does not match CC device pack server handles mismatch and will
        NOT set. If device ID is not found server handles mismatch and will NOT set.

        Args:
            *args[0] (int): The ID for the device as understood by Firemon

        Return:
            bool: True if device set, False otherwise
        """
        if self._device_id:
            device_id = self._device_id
        else:
            try:
                device_id = args[0]
            except IndexError:
                raise DeviceError('Error. A device Id must be passed to set.')
        url = self.url + '/device/{device_id}/assignment/{id}'.format(
                                                        device_id=device_id,
                                                        id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('PUT {}'.format(self.url))
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        return False

    def unset_device(self, *args) -> bool:
        """ Unset a device from CollectionConfig
        Args:
            *args[0] (int): The ID for the device as understood by Firemon

        Return:
            bool: True if device unset, False otherwise
        """
        if self._device_id:
            device_id = self._device_id
        else:
            try:
                device_id = args[0]
            except IndexError:
                raise DeviceError('Error. A device Id must be passed to unset.')
        url = self.url + '/device/{device_id}/assignment'.format(
                                                            device_id=device_id)
        self.session.headers.update({'Content-Type': 'application/json'})
        if 'activatedDeviceIds' in self._config.keys():
            if deviceId in self._config['activatedDeviceIds']:
                log.debug('DELETE {}'.format(self.url))
                response = self.session.delete(url)
                if response.status_code == 204:
                    self._reload()
                    return True
        return False

    def update(self, dev_config: dict) -> bool:
        """ Pass configuration information to update CollectionConfig.

        Args:
            dev_config (dict): a dictionary containing values for a collection

        Return:
            bool: True on successful update

        Examples:
            Duplicate an existing config
            >>> cc = fm.sm.cc.duplicate(21, 'Conan the Collector')
            >>> config = cc.template()
            Create a new pattern
            >>> p = {'pattern': 'my crazy grep stuff', 'retrieveOnMatch': True,
            ... 'continueMatch': False, 'timeoutSeconds': 100}
            >>> config['changeCriterion'].append(p)
            >>> cc.update(config)
        """
        assert(isinstance(dev_config, dict)), 'Configuration needs to be a dict'
        url = self.url + '/{id}'.format(id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
        # Check if a number of no-no keys are defined and get rid of them.
        #    these could break your cc if modified
        no_no_keys = ['index',
			'createdBy',
			'createdDate',
			'devicePackArtifactId',
			'devicePackDeviceName',
			'devicePackDeviceType',
			'devicePackGroupId',
			'devicePackId',
			'devicePackVendor',
			'lastModifiedBy',
			'lastModifiedDate'
			]
        log.debug('popping no_no_keys: {}'.format(no_no_keys))
        for k in no_no_keys:
            if k in dev_config.keys():
                dev_config.pop(k)
        dev_config['id'] = self._config['id']  # for good measure make sure this is correct
        dev_config['devicePackId'] = self._config['devicePackId']  # This is required. Make sure it's correct
        log.debug('PUT {}'.format(self.url))
        response = self.session.put(url, json=dev_config)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise FiremonError("ERROR updating Collection Config! HTTP code: {}"
                            " Content {}".format(
                                            response.status_code,
                                            response.text))

    def delete(self) -> bool:
        """ Delete this CollectionConfig.   """
        url = self.url + '/{id}'.format(id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('DELETE {}'.format(self.url))
        response = self.session.delete(url)
        if response.status_code == 204:
            return True
        return False

    def template(self) -> dict:
        """ Get configuration information for CC minus the things that should
        not be changed. Add, modify, remove fields to meet needs.
        User is expected to know variable fields.

        Return:
            dict: template information for CC
        """
        template = self._config.copy()
        # Get rid of information that should not be modified
        no_no_keys = ['index',
			'createdBy',
			'createdDate',
			'devicePackArtifactId',
			'devicePackDeviceName',
			'devicePackDeviceType',
			'devicePackGroupId',
			'devicePackId',
			'devicePackVendor',
			'lastModifiedBy',
			'lastModifiedDate'
			]
        log.debug('popping no_no_keys: {}'.format(no_no_keys))
        try:
            for k in no_no_keys:
                template.pop(k)
        except KeyError:
            pass
        return template

    def __repr__(self):
        return("<CollectionConfig(id='{}', name='{}')>".format(
                                                        self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))
