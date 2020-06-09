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
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder, RequestError
from firemon_api.core.utils import _build_dict, _find_dicts_with_key
from .collectionconfigs import CollectionConfig

log = logging.getLogger(__name__)


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

    collectionConfig = CollectionConfig

    def __init__(self, api, endpoint, config):
        super().__init__(api, endpoint, config)
        self.url = '{ep}/{gid}/{aid}'.format(
                                            ep=self.endpoint.ep_url,
                                            gid=config['groupId'],
                                            aid=config['artifactId'])

    def update(self):
        """Nothing to update"""
        pass

    def save(self):
        """Nothing to save"""
        pass

    def layout(self):
        req = Request(
            base='{url}/layout?layoutName=layout.json'.format(url=self.url),
            session=self.session,
        )
        return req.post(None)

    def get_blob(self, name='dc.zip'):
        """Get the blob (artifact) from Device Pack

        Kwargs:
            name (str): name of the artifact (dc.zip, plugin.jar, etc)

        Return:
            bytes: your blob of stuff
        """
        url = '{url}/{blob}'.format(url=self.url, blob=name)
        log.debug('GET: {}'.format(url))
        resp = self.session.get(url)
        if resp.status_code == 200:
            return resp.content
        else:
            raise RequestError(resp)


    def template(self):
        """ Get default template format for a device. Note that a number of fields
        can take bad information, like empty strings, '', and Secmanager appears
        to happily create devices and things will appear to work. Problems may
        arise on device update calls though where other parts of the system
        further check and error out.

        Return:
            dict: template information for a device with defaults included
        """

        resp = self.layout()

        template = {}
        template['name'] = None
        template['description'] = None
        template['managementIp'] = None
        template['domainId'] = self.api.domain_id
        # Fix? in later versions we require a Group
        #template['dataCollectorId'] = 1  # Assuming
        #template['dataCollectorGroupId] = ''
        #template['dataCollectorGroupName'] = ''
        template['devicePack'] = {}
        template['devicePack']['artifactId'] = self.artifactId
        template['devicePack']['deviceName'] = self.deviceName
        template['devicePack']['groupId'] = self.groupId
        template['devicePack']['id'] = self.id
        template['devicePack']['type'] = self.type
        template['devicePack']['deviceType'] = self.deviceType
        template['devicePack']['version'] = self.version
        template['extendedSettingsJson'] = {}
        for response in _find_dicts_with_key("key", resp):
            template['extendedSettingsJson'][response["key"]] = None
            if "defaultValue" in response:
                template['extendedSettingsJson'][response["key"]] = response["defaultValue"]
        return template

    def __repr__(self):
        return("<DevicePack(artifactId='{}')>".format(self.artifactId))

    def __str__(self):
        return("{}".format(self.artifactId))


class DevicePacks(Endpoint):
    """ Represents the Device Packs. There is no API to query individual Device
    Packs so this is a kludge. Retrieve all DPs and query from there.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Examples:
        Get a list of all device packs
        >>> device_packs = fm.sm.dp.all()

        Get a single device pack by artifactId
        >>> dp = fm.sm.dp.get('juniper_srx')

        Get a list of device packs by config options
        >>> fm.sm.dp.filter(ssh=True)
    """
    def __init__(self, api, app, name, record=DevicePack):
        super().__init__(api, app, name, record=DevicePack)
        self.device_packs = {}

    def all(self):
        """ Get all device packs

        Examples:

        >>> device_packs = fm.sm.dp.all()
        """

        url = ('{url}/list/DEVICE_PACK/?sort=artifactId'
        '&showHidden=true'.format(url=self.ep_url))
        req = Request(
            base=url,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

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

        dp_all = self.all()
        try:
            id = args[0]
            dp_l = [dp for dp in dp_all if dp.artifactId == id]
            if len(dp_l) == 1:
                return dp_l[0]
            else:
                return None
        except IndexError:
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

        dp_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [dp for dp in dp_all if kwargs.items() <= dict(dp).items()]

    def upload(self, file: bytes):
        """ Upload device pack

        Args:
            file (bytes): the bytes to send that make a device pack

        Returns:
            bool: The return value. True for success upload, False otherwise
        """
        url = '{url}/?overwrite=true'.format(url=self.ep_url)
        self.session.headers.pop('Content-type', None)  # If "content-type" exists get rid.
        log.debug('POST {}'.format(url))
        resp = self.session.post(url, files={'devicepack.jar': file})
        if resp.status_code == 200:
            return True
        else:
            raise RequestError(resp)