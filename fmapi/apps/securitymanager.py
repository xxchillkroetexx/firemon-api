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
import os
from typing import Generator
from urllib.parse import urlencode, quote
import uuid

# Local packages
from fmapi.errors import AuthenticationError, FiremonError, LicenseError
from fmapi.errors import DeviceError, DevicePackError, VersionError
from fmapi.core.response import Record


def _find_dicts_with_key(key: str, dictionary: dict) -> Generator[dict, None, None]:
    """
    Find all dictionaries that contain a key.

    Args:
        key (str): the key value to find.
        dictionary (dict): the dictionary hiding the keys to find.

    Yield:
        dict: the dictionary containing the key
    """
    if isinstance(dictionary, dict):
        if key in dictionary.keys():
            yield dictionary
        for k, v in dictionary.items():
            if isinstance(v, dict) or isinstance(v, list):
                for response in _find_dicts_with_key(key, v):
                    yield response
    elif isinstance(dictionary, list):
        for item in dictionary:
            if isinstance(item, dict) or isinstance(item, list):
                for response in _find_dicts_with_key(key, item):
                    yield response

def _build_dict(seq: list, key: str) -> dict:
    """ Build a dictionary from a list(of dictionaries) against a given key
    https://stackoverflow.com/questions/4391697/find-the-index-of-a-dict-within-a-list-by-matching-the-dicts-value

    Args:
        seq (list): a list of dictionaries
        key (str): the key value that is found in the dictionaries

    Retrun:
        dict: a dictionary with the index value of the list, key value, and the stuff.
    """
    return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))


class SecurityManager(object):
    """ Represents Security Manager in Firemon

    Args:
        api (obj): FiremonAPI()

    Valid attributes are:
        * cc: CollectionConfigs()
        * centralsyslogs: CentralSyslogs()
        * collectors: Collectors()
        * devices: Devices()
        * dp: DevicePacks()
        * revisions: Revisions()
        * users: Users()
        * Todo: add more as needed
    """

    def __init__(self, api):
        self.api = api
        self.session = api.session
        #self.domainId = api.domainId
        #self._url = api.base_url  # Prevoius level URL
        self.sm_url = "{url}/securitymanager/api".format(url=api.base_url)

        self._verify_domain(self.api.domainId)

        # Endpoints
        self.cc = CollectionConfigs(self)
        self.centralsyslogs = CentralSyslogs(self)
        self.collectors = Collectors(self)
        self.devices = Devices(self)
        self.dp = DevicePacks(self)  # Todo: create the other /plugins
        self.revisions = Revisions(self)
        self.users = Users(self)

    def _verify_domain(self, id):
        """ Verify that requested domain Id exists.
        Set the domain_url to pass around.
        Set the domainId that will be used.
        """
        self.domain_url = self.sm_url + "/domain/{id}".format(id=str(id))
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(self.domain_url)
        if response.status_code == 200:
            resp = response.json()
            #self.domainId = resp['id']
            self.api.domainName = resp['name']
            self.api.domainDescription = resp['description']
        else:
            raise FiremonError('Domain {} is not valid'.format(id))

    def __repr__(self):
        return("<Security Manager(url='{}')>".format(self.sm_url))

    def __str__(self):
        return('{}'.format(self.sm_url))


class DevicePacks(object):
    """ Represents the Device Packs. There is no API to query individual Device Packs
    so this is a kludge. Retrieve all DPs and query from there.

    Args:
        sm (obj): SecurityManager

    Examples:
        Get a list of all device packs
        >>> device_packs = fm.sm.dp.all()

        Get a single device pack by artifactId
        >>> dp = fm.sm.dp.get('juniper_srx')

        Get a list of device packs by config options
        >>> fm.sm.dp.filter(ssh=True)
    """
    def __init__(self, sm):
        self.sm = sm
        self.session = sm.session
        self.url = "{sm_url}/plugin".format(sm_url=sm.sm_url)
        self.device_packs = {}

    def _get_all(self) -> list:
        """ Retrieve a dictionary of installed device packs.

        Returns:
            list: a list of dictionary objects that contain device pack info
        """
        url = self.url + '/list/DEVICE_PACK/?sort=artifactId&pageSize=100&showHidden=true'
        response = self.session.get(url)
        if response.status_code == 200:
            dps = response.json()['results']
            self.device_packs = _build_dict(dps, 'artifactId')
        else:
            raise FiremonError("ERROR retrieving list of device packs! HTTP "
                               "code: {}  Server response: ".format(
                                response.status_code, response.text))

    def all(self):
        """ Get all device packs

        Examples:

        >>> device_packs = fm.sm.dp.all()
        """

        # Commentting out to avoid potential issues if a change on server occurs
        #    prior to this instance being torn down.
        #if not self.device_packs:
        #    self._get_all()
        self._get_all()
        return [DevicePack(self, self.device_packs[dp]) for dp in self.device_packs]

    def get(self, *args, **kwargs):
        """ Query and retrieve individual DevicePack

        Args:
            *args: device pack name (artifactId)
            **kwargs: key value pairs in a device pack dictionary

        Return:
            DevicePack(object): a DevicePack(object)

        Examples:

        >>> fm.sm.dp.get('juniper_srx')
        juniper_srx
        >>> fm.sm.dp.get(groupId='com.fm.sm.dp.juniper_srx')
        juniper_srx
        """
        # Commentting out to avoid potential issues if a change on server occurs
        #    prior to this instance being torn down.
        #if not self.device_packs:
        #    self._get_all()
        self._get_all()
        try:
            id = args[0]
            devpack = self.device_packs[id]
            if devpack:
                return DevicePack(self, devpack)
            else:
                raise FiremonError("ERROR retrieving devicepack")
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
        """ Retrieve a filterd list of DevicePacks

        Args:
            **kwargs: key value pairs in a device pack dictionary

        Return:
            list: a list of DevicePack(object)

        Examples:

        >>> fm.sm.dp.filter(ssh=True)
        """
        #if not self.device_packs:
        #    self._get_all()
        self._get_all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [DevicePack(self, self.device_packs[dp]) for dp in
                self.device_packs if kwargs.items() <= self.device_packs[dp].items()]

    def upload(self, file: bytes):
        """ Upload device pack

        Args:
            file (bytes): the bytes to send that make a device pack

        Returns:
            bool: The return value. True for success upload, False otherwise
        """
        url = self.url + '/?overwrite=true'
        self.session.headers.pop('Content-type', None)  # If "content-type" exists get rid.
        response = self.session.post(url, files={'devicepack.jar': file})
        if response.status_code == 200:
            self._get_all()  # Update the current listing
            return True
        else:
            return False

    def __repr__(self):
        return("<Device Packs(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class DevicePack(Record):
    """ Representation of the device pack

    Args:
        dps (obj): DevicePacks()

    Attributes:
        * artifactId
        * groupId
        * deviceName
        * vendor
        * deviceType
        * version

    Example:
        >>> dp = fm.sm.dp.get('juniper_srx')
        >>> dp
        juniper_srx
        >>> dp.version
        '1.24.10'
    """
    def __init__(self, dps, config):
        super().__init__(dps, config)
        self.dps =  dps
        self.url = dps.url

    def template(self):
        """ Get default template format for a device. Note that a number of fields
        can take bad information, like empty strings, '', and Secmanager appears
        to happily create devices and things will appear to work. Problems may
        arise on device update calls though where other parts of the system
        further check and error out.

        Return:
            dict: template information for a device with defaults included
        """
        url = self.url + '/{groupId}/{artifactId}/layout?layoutName=layout.json'.format(
                            groupId=self.groupId, artifactId=self.artifactId)
        self.session.headers.update({'Content-Type': 'application/json'})
        r = self.session.post(url)
        template = {}
        template['name'] = None
        template['description'] = None
        template['managementIp'] = None
        template['domainId'] = self.dps.sm.api.domainId
        template['dataCollectorId'] = 1  # Assuming
        template['devicePack'] = {}
        template['devicePack']['artifactId'] = self.artifactId
        template['devicePack']['deviceName'] = self.deviceName
        template['devicePack']['groupId'] = self.groupId
        template['devicePack']['id'] = self.id
        template['devicePack']['type'] = self.type
        template['devicePack']['deviceType'] = self.deviceType
        template['devicePack']['version'] = self.version
        template['extendedSettingsJson'] = {}
        for response in _find_dicts_with_key("key", r.json()):
            template['extendedSettingsJson'][response["key"]] = None
            if "defaultValue" in response:
                template['extendedSettingsJson'][response["key"]] = response["defaultValue"]
        return template

    def __repr__(self):
        return("<DevicePack(artifactId='{}')>".format(self.artifactId))

    def __str__(self):
        return("{}".format(self.artifactId))


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


class Devices(object):
    """ Represents the Devices

    Args:
        sm (obj): SecurityManager()
    """

    def __init__(self, sm):
        self.sm = sm
        self.url = sm.domain_url + '/device'  # Devices URL
        self.session = sm.session

    def all(self):
        """ Get all devices

        Return:
            list: List of Device() Records

        Examples:
            >>> devices = fm.sm.devices.all()

            >>> fm.domainId = 3
            >>> devices = fm.sm.devices.all()
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
                    url = self.url + '?page={page}&pageSize=100'.format(page=page)
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

    def get(self, *args, **kwargs):
        """ Get single device

        Args:
            *args (int): (optional) Device id to retrieve
            **kwargs (str): (optional) see filter() for available filters

        Examples:
            Get by ID
            >>> fm.sm.devices.get(21)
            vSRX-2

            Get by partial name. Case insensative.
            >>> fm.sm.devices.get(name='SONICWAll')
            SONICWALL-TZ-210-1
        """
        try:
            id = args[0]
            url = self.url + '/{id}'.format(id=str(id))
            self.session.headers.update({'Content-Type': 'application/json'})
            response = self.session.get(url)
            if response.status_code == 200:
                return Device(self, response.json())
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
            name, description, mgmtip, vendors, products, datacosllectors,
            devicegroups, devicetypes, centralsyslogs, retrieval, change,
            log, parentids, devicepackids

        Return:
            list: List of Device() Records
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.devices.filter(name='bogus')
            [bogus-ASA-support-3101, bogus.lab.securepassage.com]

            Partial IP search.
            >>> fm.sm.devices.filter(mgmtip='10.2')
            [bogus.lab.securepassage.com, Some auto test]
        """
        if not kwargs:
            raise ValueError('filter() must be passed kwargs. ')
        total = 0
        page = 0
        count = 0
        url = self.url + '/filter?page={page}&pageSize=100&filter={filters}'.format(
                            page=page, filters=urlencode(kwargs, quote_via=quote))
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
                    url = self.url + '/filter?page={page}&pageSize=100&filter={filters}'.format(
                                    page=page, filters=urlencode(kwargs, quote_via=quote))
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

    def search(self, arg):
        """ Filter devices based on search parameters

        Args:
            arg (str): search parameter

        Return:
            list: List of Device() Records
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.devices.search('bogus')
            [bogus-ASA-support-3101, bogus.lab.securepassage.com]

            Partial IP search.
            >>> fm.sm.devices.search('10.2')
            [bogus.lab.securepassage.com, Some auto test]
        """
        total = 0
        page = 0
        count = 0
        url = self.url + '?page={page}&pageSize=100&search={filter}'.format(
                            page=page, filter=arg)
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
                    url = url = self.url + '?page={page}&pageSize=100&search={filter}'.format(
                                    page=page, filter=arg)
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

    def create(self, dev_config, retrieve: bool=False):
        """  Create a new device

        Args:
            dev_config (dict): dictionary of configuration data.
            retrieve (bool): whether to kick off a manual retrieval

        Return:
            Device (obj): a Device() of the newly created device

        Examples:
            >>> config = fm.sm.dp.get('juniper_srx').template()
            >>> config['name'] = 'Conan'
            >>> config['description'] = 'A test of the API'
            >>> config['managementIp'] = '10.2.2.2'
            >>> dev = fm.sm.devices.create(config)
            Conan
        """
        assert(isinstance(dev_config, dict)), 'Configuration needs to be a dict'
        url = self.url + '?manualRetrieval={debug}'.format(debug=str(retrieve))
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.post(url, json=dev_config)
        if response.status_code == 200:
            config = json.loads(response.content)
            return self.get(config['id'])
        else:
            raise DeviceError("ERROR installing device! HTTP code: {}  "
                              "Server response: {}".format(
                              response.status_code, response.text))

    def __repr__(self):
        return("<Devices(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class Device(Record):
    """ Represents a device in Firemon

    Args:
        devs (obj): Devices()
        config (dict): all the things

    Attributes:
        * cc (collection configs)
        * revisions

    Examples:

        Get device by ID
        >>> dev = fm.sm.devices.get(21)
        >>> dev
        vSRX-2

        Show configuration data
        >>> dict(dev)
        {'id': 21, 'domainId': 1, 'name': 'vSRX-2', 'description': 'regression test SRX', ...}

        List all collection configs that device can use
        >>> dev.cc.all()
        [21, 46]
        >>> cc = dev.cc.get(46)

        List all revisions associated with device
        >>> dev.revisions.all()
        [76, 77, 108, 177, 178]

        Get the latest revision
        >>> rev = dev.revisions.filter(latest=True)[0]
        178
    """
    def __init__(self, devs, config):
        super().__init__(devs, config)

        self.devs = devs
        self.url = devs.sm.domain_url + '/device/{id}'.format(id=str(config['id']))  # Device id URL

        # Add attributes to Record() so we can get more info
        self.revisions = Revisions(self.devs.sm, self.id)
        self.cc = CollectionConfigs(self.devs.sm, self.devicePack.id, self.id)

    def _reload(self):
        """ Todo: Get configuration info upon change """
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(self.url)
        if response.status_code == 200:
            config = response.json()
            self._config = config
            self.__init__(self.devs, self._config)
        else:
            raise FiremonError('Error! unable to reload Device')

    def delete(self, deleteChildren: bool=False, a_sync: bool=False,
                    sendNotification: bool=False, postProcessing: bool=True):
        """ Delete the device (and child devices)

        Kwargs:
            deleteChildren (bool): delete all associated child devices
            a_sync (bool): ???
            sendNotification (bool): ???
            postProcessing (bool): ???

        Example:
            >>> dev = fm.sm.devices.get(17)
            >>> dev
            CSM-2

            Delete device and all child devices
            >>> dev.delete(deleteChildren=True)
            True
        """

        kwargs = {'deleteChildren': deleteChildren, 'async': a_sync,
                  'sendNotification': sendNotification, 'postProcessing': postProcessing}
        url = self.url + '?{filters}'.format(filters=urlencode(kwargs, quote_via=quote))
        response = self.session.delete(url)
        if response.status_code == 200:
            return True
        else:
            raise DeviceError("ERROR deleting device(s)! Code {}".format(response.status_code))

    def import_config(self, f_list: list) -> bool:
        """ Import config files for device to create a new revision

        Args:
            f_list (list): a list of tuples. Tuples are intended to uploaded
                as a multipart form using 'requests'. format of the data in the
                tuple is ('file', ('<file-name>', open(<path_to_file>, 'rb'), 'text/plain'))

        Example:
            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> dir = '/path/to/config/files/'
            >>> f_list = []
            >>> for fn in os.listdir(dir):
            ... 	path = os.path.join(dir, fn)
            ... 	f_list.append(('file', (fn, open(path, 'rb'), 'text/plain')))
            >>> dev.import_config(f_list)
        """
        self.session.headers.update({'Content-Type': 'multipart/form-data'})
        changeUser = self.devs.sm.api.username  # Not really needed
        correlationId = str(uuid.uuid1())  # Not really needed
        url = self.url + '/rev?action=IMPORT&changeUser={}&correlationId={}'.format(
            changeUser, correlationId)  # changeUser and corId not need
        response = self.session.post(url, files=f_list)
        if response.status_code == 200:
            self.session.headers.pop('Content-type', None)
            return True
        else:
            raise FiremonError('Error: unable to upload configuration files! HTTP code: {} \
                            Content {}'.format(response.status_code, response.text))

    def import_support(self, zip_file: bytes, renormalize: bool=False):
        """ Todo: Import a 'support' file, a zip file with the expected device
        config files along with 'NORMALIZED' and meta-data files. Use this
        function and set 'renormalize = True' and mimic 'import_config'.

        NOTE: Device packs must match from the support files descriptor.json

        Args:
            zip_file (bytes): bytes that make a zip file

        Kwargs:
            renormalize (bool): defualt (False). Tell system to re-normalize from
                config (True) or use imported 'NORMALIZED' files (False)

        Example:
            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> fn = '/path/to/file/vsrx-2.zip'
            >>> with open(fn, 'rb') as f:
            >>>     zip_file = f.read()
            >>> dev.import_support(zip_file)
        """
        self.session.headers.update({'Content-Type': 'multipart/form-data'})
        url = self.url + '/import?renormalize={}'.format(str(renormalize))
        files = {'file': zip_file}
        response = self.session.post(url, files=files)
        if response.status_code == 200:
            self.session.headers.pop('Content-type', None)
            return True
        else:
            raise FiremonError('Error: unable to upload zip file! HTTP code: {} \
                            Content {}'.format(response.status_code, response.text))

    def update(self, dev_config: dict, retrieve: bool=False) -> bool:
        """ Pass configuration information to update Device.

        Args:
            dev_config (dict): a dictionary containing values for a collection

        Kwargs:
            retrieve (bool): whether to kick off a manual retrieval

        Return:
            bool: True on successful update

        Examples:

            Update from dictionary

            >>> dev = fm.sm.devices.get(1)
            >>> config = dev.template()
            Modify config
            >>> config['description'] = 'internal test device'
            >>> dev.update(config)

            Update self

            >>> dev = fm.sm.devices.get(1)
            >>> dev.description = 'A random test device'
            >>> dev.update(dict(dev))
        """
        assert(isinstance(dev_config, dict)), 'Configuration needs to be a dict'
        dev_config['id'] = self._config['id']  # make sure this is set appropriately
        dev_config['devicePack'] = self._config['devicePack']  # Put all this redundant shit back in
        url = self.url + '?manualRetrieval={retrieval}'.format(retrieval=str(retrieve))
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url, json=dev_config)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR updating Device! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def template(self) -> dict:
        """ Dump out current config information that can be modified and sent
        to update() current device

        Return:
            dict: current device configuration minus things that should not be touched
        """
        config = self._config.copy()
        no_no_keys = ['devicePack',
        'securityConcernIndex',
        'gpcComputeDate',
        'gpcDirtyDate',
        'gpcImplementDate',
        'gpcStatus'
        ]
        for k in no_no_keys:
            config.pop(k)

        config['devicePack'] = {'artifactId': self._config['devicePack']['artifactId']}
        return config

    def do_retrieval(self, debug: bool=False):
        """ Have current device begin a manual retrieval.

        Kwargs:
            debug (bool): ???
        """
        url = self.url + '/manualretrieval?debug={debug}'.format(debug=str(debug))
        response = self.session.post(url)
        if response.status_code == 204:
            return True
        else:
            return False

    def rule_usage(self, type: str='total'):
        """ This appears to be a very generic bit of information. Purely the
        total hits for all rules on the device.

        Kwargs:
            total (str): either 'total' or 'daily'

        Return:
            json: daily == {'hitDate': '....', 'totalHits': int}
                  total == {'totalHits': int}
        """
        url = self.url + '/ruleusagestat/{type}'.format(type=type)
        self.session.headers.update({'Accept': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise FiremonError('Error: Unable to retrieve device rule usage info')

    def get_nd_latest(self):
        """Gets the latest revision as a fully parsed object """
        url = self.url + '/rev/latest/nd/all'
        self.session.headers.update({'Accept': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            return ParsedRevision(self.devs, response.json())
        else:
            raise FiremonError('Error: Unable to retrieve latest parsed revision')

    def __repr__(self):
        return("<Device(id='{}', name={})>".format(self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))


class Revisions(object):
    """ Represents the Revisions.
    Filtering is terrible given the API. It is a mixture of revID,
    static domain requirements and deviceID, or searching by a weird subset
    of our internal SIQL (but you cannot search by name or anything in SIQL). As a
    kludge I just ingest all revisions (like the device packs) and create get() and
    filter() functions to parse a dictionary. This may be problematic if there
    are crazy number of revisions but since this is for interal use *meh*.

    Args:
        sm (object): SecurityManager()

    Kwargs:
        deviceId (int): Device id

    Examples:
        >>> rev = fm.sm.revisions.get(34)
        >>> rev = fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')[0]
    """
    def __init__(self, sm, deviceId: int=None):
        self.sm = sm
        self.session = sm.session
        self.url = "{sm_url}/rev".format(sm_url=sm.sm_url)
        # Use setter. Intended for use when Revisions is called from Device(objects)
        self._deviceId = deviceId
        self._revisions = {}

    def _get_all(self):
        """ Retrieve a dictionary of revisions. This is effectively a kludge since we do not
        have direct access to /rev endpoint so we will injest all then parse locally

        Returns:
            dict: a dictionary that contains revision info
        """
        total = 0
        page = 0
        count = 0
        if self.deviceId:
            url = self.sm.domain_url + \
                '/device/{deviceId}/rev?sort=id&page={page}&pageSize=100'.format(
                deviceId=self.deviceId, page=page)
        else:
            url = self.sm.domain_url + \
                '/rev?sort=id&page={page}&pageSize=100'.format(page=page)
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
                    if self.deviceId:
                        url = self.sm.domain_url + \
                            'device/{deviceId}/rev?sort=id&page={page}&pageSize=100'.format(
                            deviceId=self.deviceId, page=page)
                    else:
                        url = self.sm.domain_url + \
                            '/rev?sort=id&page={page}&pageSize=100'.format(page=page)
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                self._revisions = _build_dict(results, 'id')
            else:
                self._revisions = {}
        else:
            raise FiremonError("ERROR retrieving revisions! HTTP code: {}  "
                              "Server response: {}".format(
                              response.status_code, response.text))

    def all(self):
        """ Get all revisions

        Return:
            list: a list of Revision(object)

        Examples:

            >>> revs = fm.sm.revisions.all()
        """
        #if not self._revisions:
        #    self._get_all()
        self._get_all()
        return [Revision(self, self._revisions[id]) for id in self._revisions]

    def get(self, *args, **kwargs):
        """ Query and retrieve individual Revision

        Args:
            *args (int): The revision ID
            **kwargs: key value pairs in a revision dictionary

        Return:
            Revision(object): a single Revision(object)

        Examples:

            >>> fm.sm.revisions.get(3)
            3
            >>> rev = fm.sm.revisions.get(3)
            >>> type(rev)
            <class 'fmapi.apps.securitymanager.Revision'>
            >>> rev = fm.sm.revisions.get(correlationId='7a5406e4-93de-44af-8ed1-0e4135458324')
            >>> rev
            11
        """
        #if not self._revisions:
        #    self._get_all()
        self._get_all()
        try:
            id = args[0]
            rev = self._revisions[id]
            if rev:
                return Revision(self, rev)
            else:
                raise FiremonError("ERROR retrieving revison")
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
        """ Retrieve a filterd list of Revisions

        Args:
            **kwargs: key value pairs in a revision dictionary

        Return:
            list: a list of Revision(object)

        Examples:

            >>> fm.sm.revisions.filter(deviceName='vSRX-2')
            [76, 77, 108, 177, 178]

            >>> fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')
            [178]

            >>> fm.sm.revisions.filter(deviceType='FIREWALL')
            [3, 4, 5, 6, 7, 8, 9,

            >>> fm.sm.revisions.filter(latest=True)
            [1, 2, 3, 6, 8, 9, 10, 13, 14, 75, 122, 153, 171, 174, 178, 189]
        """
        #if not self._revisions:
        #    self._get_all()
        self._get_all()

        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [Revision(self, self._revisions[id]) for id in
                self._revisions if kwargs.items() <= self._revisions[id].items()]

    @property
    def deviceId(self):
        return self._deviceId

    @deviceId.setter
    def deviceId(self, id):
        self._deviceId = id

    def __repr__(self):
        return("<Revisions(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class Revision(Record):
    """ Represents a Revision in Firemon
    The API is painful to use. In some cases the info needed is under 'ndrevisions'
    and it other cases it is under 'normalization'. And different paths can get
    the exact same information.

    (change configuration &/or normalization state)

    Args:
        revs: Revisions() object
        config (dict): all the things

    Examples:
        >>> rev = fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')[0]
        >>> zip = rev.export()
        >>> with open('export.zip', 'wb') as f:
        ...   f.write(zip)
        ...
        36915
        >>> zip = rev.export(with_meta=False)
        >>> rev.delete()
        True
    """
    def __init__(self, revs, config):
        super().__init__(revs, config)
        self.revs = revs
        self.url = revs.sm.sm_url + '/rev/{revId}'.format(revId=str(config['id']))
        # Because instead of just operating on the revision they needed another path <sigh>
        self.url2 = revs.sm.domain_url + '/device/{deviceId}/rev/{revId}'.format(\
                    deviceId=str(config['deviceId']), revId=str(config['id']))

    def summary(self):
        return self._config

    def changelog(self):
        """ Revision changelog """
        total = 0
        page = 0
        count = 0
        url = self.url2 + '/changelog?page={page}&pageSize=100'.format(page=page)
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
                    url = self.url2 + '/changelog?page={page}&pageSize=100'.format(page=page)
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                return(results)
            else:
                return([])
        else:
            raise FiremonError("ERROR retrieving revisions! HTTP code: {}  "
                              "Server response: {}".format(
                              response.status_code, response.text))

    def export(self, with_meta: bool=True):
        """ Export a zip file contain the config data for the device and,
        optionally, other meta data and NORMALIZED data. Support files in gui.

        Kwargs:
            with_meta (bool): Include metadata and NORMALIZED config files

        Return:
            bytes: zip file
        """
        self.session.headers.pop('Content-type', None)  # If "content-type" exists get rid.
        if with_meta:
            url = self.url + '/export'
        else:
            url = self.url + '/export/config'
        response = self.session.get(url)
        if response.status_code == 200:
            return response.content
        else:
            raise FiremonError("ERROR retrieving revisions! HTTP code: {}  "
                              "Server response: {}".format(
                              response.status_code, response.text))

    def delete(self):
        """ Delete the revision

        Return:
            bool: True if deleted
        """
        url = self.revs.sm.domain_url + \
            '/device/{deviceId}/rev/{revId}'.format(
                deviceId=str(self.deviceId), revId=str(self.id))
        response = self.session.delete(url)
        if response.status_code == 204:
            return True
        else:
            raise DeviceError("ERROR deleting revision id {}".format(self.id))

    def get_nd(self):
        """Get normalized data as a fully parsed object """
        url = self.url + '/nd/all'
        self.session.headers.update({'Accept': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            return ParsedRevision(self.revs, response.json())
        else:
            raise FiremonError('Error: Unable to retrieve parsed revision')

    def __repr__(self):
        return("<Revision(id='{}', device='{}')>".format(self.id, self.deviceId))

    def __str__(self):
        return("{}".format(self.id))


class ParsedRevision(Record):
    """A dynamic representation of all the NORMALIZED things

    Todo:
        Document the JSON/Record information and key values purpose
            or at least some of the major ones
    """
    def __repr__(self):
        return("ParsedRevision<(id='{}')>".format(self.revisionId))

    def __str__(self):
        return("{}".format(self.revisionId))


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


class Users(object):
    """ Represents the Users

    Args:
        sm (obj): SecurityManager object
    """

    def __init__(self, sm):
        self.sm = sm
        self.url = sm.domain_url + '/user'  # user URL
        self.session = sm.session

    def all(self):
        """ Get all users

        Return:
            list: List of User(object)

        Raises:
            fmapi.errors.FiremonError: if not status code 200

        Examples:
            >>> users = fm.sm.users.all()
            [..., ..., ..., ..., ]
        """
        url = self.url + '?includeSystem=true&includeDisabled=true&sort=id&pageSize=100'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                return [User(self, user) for user in resp['results']]
            else:
                return None
        else:
            raise FiremonError("ERROR retrieving user! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def get(self, *args, **kwargs):
        """ Get single user

        Args:
            *args (int, optional): User id to retrieve
            **kwargs (str, optional): see filter() for available filters

        Raises:
            fmapi.errors.FiremonError: if not status code 200

        Examples:
            Get by ID
            >>> fm.sm.users.get(2)
            ...
        """
        try:
            id = args[0]
            url = self.url + '/{id}'.format(id=str(id))
            self.session.headers.update({'Content-Type': 'application/json'})
            response = self.session.get(url)
            if response.status_code == 200:
                return User(self, response.json())
            else:
                raise FiremonError("ERROR retrieving user! HTTP code: {}"
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
        """ Filter users based on search parameters

        Args:
            **kwargs (str): filter parameters

        Available Filters:
            username, firstName, lastName, email,
            passwordExpired, locked, expired, enabled

        Return:
            list: List of User(objects)
            None: if not found

        Raises:
            fmapi.errors.DeviceError: if not status code 200

        Examples:
            Partial name search return multiple users
            >>> fm.sm.users.filter(username='socra')
            [<User(id='4', username=dc_socrates)>, <User(id='3', username=nd_socrates)>]

            >>> fm.sm.users.filter(enabled=False)
            [<User(id='2', username=workflow)>]

            >>> fm.sm.users.filter(locked=True)
            [<User(id='2', username=workflow)>]
        """
        if not kwargs:
            raise ValueError('filter() must be passed kwargs. ')
        total = 0
        page = 0
        count = 0
        url = self.url + '/filter?page={page}&pageSize=100&filter={filters}'.format(
                            page=page, filters=urlencode(kwargs, quote_via=quote))
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
                    url = self.url + '/filter?page={page}&pageSize=100&filter={filters}'.format(
                                    page=page, filters=urlencode(kwargs, quote_via=quote))
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                return [User(self, user) for user in results]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving users! HTTP code: {}"
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
        return("<Users(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class User(Record):
    """ Represents a User in Firemon

    Args:
        usrs (obj): Users() object
        config (dict): all the things
    """
    def __init__(self, usrs, config):
        super().__init__(usrs, config)

        self.usrs = usrs
        self.url = usrs.sm.domain_url + '/user/{id}'.format(id=str(config['id']))  # User id URL

    def _reload(self):
        """ Todo: Get configuration info upon change """
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(self.url)
        if response.status_code == 200:
            config = response.json()
            self._config = config
            self.__init__(self.api, self._config)
        else:
            raise FiremonError('Error! unable to reload User')

    def enable(self):
        url = self.url + '/enable'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR enableing User! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def disable(self):
        url = self.url + '/disable'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR disabling User! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def unlock(self):
        url = self.url + '/unlock'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR unlocking User! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def update(self):
        pass

    def __repr__(self):
        return("<User(id='{}', username={})>".format(self.id, self.username))

    def __str__(self):
        return("{}".format(self.username))


class UserGroup(Record):
    """ Represents a UserGroup in Firemon

    Args:
        usrs (obj): Users() object
        config (dict): all the things

    Todo:
        Finish this -
    """
    def __init__(self, usrs, config):
        super().__init__(usrs, config)

        self.usrs = usrs
        self.url = usrs.sm.domain_url + '/user/{id}'.format(id=str(config['id']))  # User id URL
