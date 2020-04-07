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
from firemon_api.core.utils import _build_dict, _find_dicts_with_key

log = logging.getLogger(__name__)


class DevicePacks(object):
    """ Represents the Device Packs. There is no API to query individual Device
    Packs so this is a kludge. Retrieve all DPs and query from there.

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
        url = self.url + ('/list/DEVICE_PACK/?sort=artifactId&pageSize='
                        '100&showHidden=true')
        log.debug('GET {}'.format(self.url))
        response = self.session.get(url)
        if response.status_code == 200:
            dps = response.json()['results']
            self.device_packs = _build_dict(dps, 'artifactId')
        else:
            raise FiremonError("ERROR retrieving list of device packs! HTTP "
                               "code: {}  Server response: ".format(
                                                        response.status_code,
                                                        response.text))

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
        return [DevicePack(self, self.device_packs[dp])
                for dp in self.device_packs]

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
                self.device_packs if kwargs.items()
                <= self.device_packs[dp].items()]

    def upload(self, file: bytes):
        """ Upload device pack

        Args:
            file (bytes): the bytes to send that make a device pack

        Returns:
            bool: The return value. True for success upload, False otherwise
        """
        url = self.url + '/?overwrite=true'
        self.session.headers.pop('Content-type', None)  # If "content-type" exists get rid.
        log.debug('POST {}'.format(self.url))
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
        self.dps = dps
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
        url = self.url + ('/{groupId}/{artifactId}/layout?'
                        'layoutName=layout.json'.format(
                                                groupId=self.groupId,
                                                artifactId=self.artifactId))
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('POST {}'.format(self.url))
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
