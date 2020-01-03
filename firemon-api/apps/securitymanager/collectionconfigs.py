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
from fmapi.core.utils import _build_dict


class CollectionConfigs(object):
    """ Represents the Collection Configs
    Filtering is terrible given the API.
    As a kludge I just injest all collectionconfigs (like the device packs) and create
    get() and filter() functions to parse a dictionary.

    Args:
        sm (obj): SecurityManager() object

    Kwargs:
        devicePackId (int): Device Pack id
        deviceId (int): Device id

    Examples:
        >>> cc = fm.sm.cc.get(46)
        >>> cc = fm.sm.cc.filter(activatedForDevicePack=True, devicePackArtifactId='juniper_srx')[0]
    """
    def __init__(self, sm, devicePackId: int=None, deviceId: int=None):
        self.sm = sm
        self.url = sm.sm_url + '/collectionconfig'  # Collection Config URL
        self.session = sm.session
        # Use setter. Intended for use when CollectionConfigs() is called from Device()
        self._devicePackId = devicePackId
        self._deviceId = deviceId

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
        if self.devicePackId:
            url = self.url + '?devicePackId={devicePackId}&page={page}&pageSize=100'.format(
                                        devicePackId=self.devicePackId, page=page)
        else:
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
                    url = url = self.url + '?sort=devicePack.vendor&page={page}&pageSize=100'.format(page=page)
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
        return [CollectionConfig(self, self._collectionconfigs[id]) for id in self._collectionconfigs]

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
            <class 'fmapi.apps.securitymanager.CollectionConfig'>
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
                raise FiremonError("ERROR retrieving collectionconfig. CC does not exist")
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

            >>> fm.sm.cc.filter(activatedForDevicePack=True, devicePackId=40)
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
                self._collectionconfigs if kwargs.items() <= self._collectionconfigs[id].items()]

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
        response = self.session.post(self.url, json=dev_config)
        if response.status_code == 200:
            config = json.loads(response.content)
            return self.get(config['id'])
        else:
            raise DeviceError("ERROR creating Collection Config! HTTP code: {}  "
                              "Server response: {}".format(
                              response.status_code, response.text))

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
        response = self.session.post(self.url, json=config)
        if response.status_code == 200:
            config = json.loads(response.content)
            return self.get(config['id'])
        else:
            raise FiremonError("ERROR creating Collection Config! HTTP code: {}  "
                              "Server response: {}".format(
                              response.status_code, response.text))

    @property
    def devicePackId(self):
        return self._devicePackId

    @devicePackId.setter
    def deviceId(self, id):
        self._devicePackId = id

    @property
    def deviceId(self):
        return self._deviceId

    @deviceId.setter
    def deviceId(self, id):
        self._deviceId = id

    def __repr__(self):
        return("<CollectionConfigs(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


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
        {'id': 47, 'name': 'Ape Grape', 'devicePackId': 40, ...}

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
        self._deviceId = ccs._deviceId  # Should be 'None' unless coming through Device()
        self.url = ccs.url  # cc URL

    def _reload(self):
        url = self.url + '/{id}'.format(id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            config = response.json()
            self._config = config
            self.__init__(self.api, self._config)
        else:
            raise FiremonError('Error! unable to reload collection config')

    def set_dp(self) -> bool:
        """ Set CollectionConfig for Device Pack assignment. """
        url = self.url + '/devicepack/{devicePackId}/assignment/{id}'.format(
                                    devicePackId=self.devicePackId, id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        return False

    def unset_dp(self) -> bool:
        """ Unset CollectionConfig for Device Pack assignment.
        Effectively sets back to 'default'
        """
        url = self.url + '/devicepack/{devicePackId}/assignment'.format(
                                            devicePackId=self.devicePackId)
        self.session.headers.update({'Content-Type': 'application/json'})
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
        if self._deviceId:
            deviceId = self._deviceId
        else:
            try:
                deviceId = args[0]
            except IndexError:
                raise DeviceError('Error. A device Id must be passed to set.')
        url = self.url + '/device/{deviceId}/assignment/{id}'.format(deviceId=deviceId, id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
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
        if self._deviceId:
            deviceId = self._deviceId
        else:
            try:
                deviceId = args[0]
            except IndexError:
                raise DeviceError('Error. A device Id must be passed to unset.')
        url = self.url + '/device/{deviceId}/assignment'.format(deviceId=deviceId)
        self.session.headers.update({'Content-Type': 'application/json'})
        if 'activatedDeviceIds' in self._config.keys():
            if deviceId in self._config['activatedDeviceIds']:
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
        for k in no_no_keys:
            if k in dev_config.keys():
                dev_config.pop(k)
        dev_config['id'] = self._config['id']  # for good measure make sure this is correct
        dev_config['devicePackId'] = self._config['devicePackId']  # This is required. Make sure it's correct
        response = self.session.put(url, json=dev_config)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise FiremonError("ERROR updating Collection Config! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def delete(self) -> bool:
        """ Delete this CollectionConfig.   """
        url = self.url + '/{id}'.format(id=self.id)
        self.session.headers.update({'Content-Type': 'application/json'})
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
        try:
            for k in no_no_keys:
                template.pop(k)
        except KeyError:
            pass
        return template

    def __repr__(self):
        return("<CollectionConfig(id='{}', name='{}')>".format(self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))
