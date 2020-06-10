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
from urllib.parse import urlencode, quote
import uuid

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder, RequestError
from .devicepacks import DevicePack
from .collectionconfigs import CollectionConfigs, CollectionConfig
from .revisions import Revisions, Revision, ParsedRevision

log = logging.getLogger(__name__)


class Device(Record):
    """Device Record

    Args:
        api (obj): FiremonAPI()
        endpoint (obj): Endpoint()
        config (dict): dictionary of things values from json

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
        {'id': 21, 'domainId': 1, 'name': 'vSRX-2',
            'description': 'regression test SRX', ...}

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

    extendedSettingsJson = JsonField
    devicePack = DevicePack

    def __init__(self, api, endpoint, config):
        super().__init__(api, endpoint, config)
        self.url = '{ep}/{id}'.format(ep=self.endpoint.ep_url, 
                                      id=config['id'])

        # Add attributes to Record() so we can get more info
        self.revisions = Revisions(self.api, 
                                   self.endpoint.app, 
                                   'rev',
                                   device_id=config['id'])
        #self.revisions = Revisions(self.devs.sm, self.id)
        #self.cc = CollectionConfigs(self.devs.sm, self.devicePack.id, self.id)
        self.collectionconfigs = CollectionConfigs(self.api, 
                                   self.endpoint.app, 
                                   'collectionconfig',
                                   device_id=config['id'])

    def save(self, retrieve: bool=False) -> bool:
        """Saves changes to an existing object.
        Checks the state of `_diff` and sends the entire
        `serialize` to Request.put().

        Kwargs:
            retrieve (bool): Perform manual retrieval on save

        Return:
            (bool): True if PUT request was successful.

        >>> dev = fm.sm.devices.get(name='vsrx3')
        >>> dev.description
        AttributeError: 'Device' object has no attribute 'description'
        >>> dev.attr_set('description','Virtual SRX - DC 3')
        >>> dev.save()
        True
        >>>
        """
        if self.id:
            diff = self._diff()
            if diff:
                serialized = self.serialize()
                # Make sure this is set appropriately. Cannot change.
                serialized['id'] = self._config['id']
                # Put all this redundant nonsense back in. Why api, why?
                serialized['devicePack'] = self._config['devicePack']
                url = '{url}?manualRetrieval={retrieval}'.format(
                                                    url=self.url,
                                                    retrieval=str(retrieve))
                req = Request(
                    base=url,
                    session=self.session,
                )
                if req.put(serialized):
                    return True

        return False

    def update(self, data: dict, retrieve: bool=False) -> bool:
        """Update an object with a dictionary.
        Accepts a dict and uses it to update the record and call save().
        For nested and choice fields you'd pass an int the same as
        if you were modifying the attribute and calling save().

        Args:
            data (dict): Dictionary containing the k/v to update the
            record object with.

        Returns:
            bool: True if PUT request was successful.

        Example:
        >>> dev = fm.sm.devices.get(1)
        >>> dev.update({
        ...   "name": "foo2",
        ...   "description": "barbarbaaaaar",
        ... })
        True
        """

        for k, v in data.items():
            self.attr_set(k, v)
        return self.save(retrieve=retrieve)

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
                  'sendNotification': sendNotification,
                  'postProcessing': postProcessing}
        url = '{url}?{filters}'.format(url=self.url,
                                    filters=urlencode(kwargs, 
                                                    quote_via=quote))
        req = Request(
            base=url,
            session=self.session,
        )
        if req.delete():
            return True

    def rev_export(self, meta: bool=True):
        """Export latest configuration files as a zip file 
        
        Support files include all NORMALIZED data and other meta data.
        Raw configs include only those files as found by Firemon 
        during a retrieval.
        
        Kwargs:
            meta (bool): True gets a SUPPORT file. False is Raw only

        Returns:
            bytes: file

        Example:
            >>> import os
            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> support = dev.rev_export()
            >>> with open('support.zip', 'wb') as f:
            ...   f.write(support)
            ...
            38047
        """
        if meta:
            url = '{url}/export'.format(url=self.url)
        else:
            url = '{url}/export/config'.format(url=self.url)
        response = self.session.get(url)
        if response.status_code == 200:
            return response.content
        else:
            raise RequestError(response)

    def import_config(self, f_list: list) -> bool:
        """Import config files for device to create a new revision

        Args:
            f_list (list): a list of tuples. Tuples are intended to uploaded
            as a multipart form using 'requests'. format of the data in the
            tuple is:
            ('file', ('<file-name>', open(<path_to_file>, 'rb'), 'text/plain'))

        Example:
            >>> import os
            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> dir = '/path/to/config/files/'
            >>> f_list = []
            >>> for fn in os.listdir(dir):
            ...     path = os.path.join(dir, fn)
            ...     f_list.append(('file', (fn, open(path, 'rb'), 'text/plain')))
            >>> dev.import_config(f_list)
        """
        self.session.headers.update({'Content-Type': 'multipart/form-data'})
        changeUser = self.api.username  # Not really needed
        correlationId = str(uuid.uuid1())  # Not really needed
        url = ('{url}/rev?action=IMPORT&changeUser={cu}'
                        '&correlationId={ci}'.format(url=self.url,
                                                     cu=changeUser,
                                                     ci=correlationId))
        log.debug('POST {}'.format(self.url))
        response = self.session.post(url, files=f_list)
        self.session.headers.pop('Content-type', None)
        if response.status_code == 200:
            return True
        else:
            raise RequestError(response)

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
        url = '{url}/import?renormalize={tonorm}'.format(url=self.url,
                                                    tonorm=str(renormalize))
        files = {'file': zip_file}
        log.debug('POST {}'.format(self.url))
        response = self.session.post(url, files=files)
        self.session.headers.pop('Content-type', None)
        if response.status_code == 200:
            return True
        else:
            raise RequestError(response)

    def exec_retrieval(self, debug: bool=False):
        """Have current device begin a manual retrieval.

        Kwargs:
            debug (bool): ???
        """
        url = '{url}/manualretrieval?debug={debug}'.format(url=self.url,
                                                           debug=str(debug))
        req = Request(
            base=url,
            session=self.session,
        )
        if req.post(None):
            return True

    def rule_usage(self, type: str='total'):
        """Get rule usage for device.
        total hits for all rules on the device.

        Kwargs:
            type (str): either 'total' or 'daily'

        Return:
            json: daily == {'hitDate': '....', 'totalHits': int}
                  total == {'totalHits': int}
        """
        url = '{url}/ruleusagestat/{type}'.format(url=self.url,
                                                    type=type)
        req = Request(
            base=url,
            session=self.session,
        )
        return req.get()

    def nd_problem(self):
        """Retrieve problems with latest normalization
        """
        url = '{url}/device/{id}/nd/problem'.format(url=self.app_url,
                                                    id=self.id)
        req = Request(
            base=url,
            session=self.session,
        )
        return req.get()

    def get_nd_latest(self):
        """Gets the latest revision as a fully parsed object """
        url = self.url + '/rev/latest/nd/all'
        self.session.headers.update({'Accept': 'application/json'})
        log.debug('GET {}'.format(self.url))
        response = self.session.get(url)
        if response.status_code == 200:
            return ParsedRevision(self.devs, response.json())
        else:
            raise FiremonError('Error: Unable to retrieve latest parsed '
                                'revision')

    def ssh_key_remove(self):
        """Remove ssh key from all Collectors for Device.

        Notes:
            SSH Key location: /var/lib/firemon/dc/.ssh/known_hosts
        """
        url = '{url}/sshhostkey'.format(url=self.url)
        req = Request(
            base=url,
            session=self.session,
        )
        if req.put(None):
            return True

    def __repr__(self):
        if len(str(self.id)) > 10:
            id = '{}...'.format(self.id[0:9])
        else:
            id = self.id
        if len(self.name) > 10:
            name = '{}...'.format(self.name[0:9])
        else:
            name = self.name
        return("<Device(id='{}', name='{}')>".format(id, name))

    def __str__(self):
        return("{}".format(self.name))


class Devices(Endpoint):
    """ Represents the Devices

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        record (obj): default `Record` object
        collector_id (int): Data Collector id
        collectorgroup_id (str): Data Collector Group Id (uuid)
    """

    def __init__(self, api, app, name, record=Device):
        super().__init__(api, app, name, record=Device)

        self.ep_url = "{url}/{ep}".format(url=app.domain_url,
                                        ep=name)

        self.ep_url = "{url}/{ep}".format(url=app.domain_url, ep=name)        


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
        url = self.url + '?manualRetrieval={retrieve}'.format(
                                                        retrieve=str(retrieve))
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('POST {}'.format(self.url))
        response = self.session.post(url, json=dev_config)
        if response.status_code == 200:
            config = json.loads(response.content)
            return self.get(config['id'])
        else:
            raise DeviceError("ERROR installing device! HTTP code: {}  "
                              "Server response: {}".format(
                                            response.status_code,
                                            response.text))