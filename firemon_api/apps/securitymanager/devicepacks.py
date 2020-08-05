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
        config (dict): dictionary of things values from json
        app (obj): App()

    Example:
        >>> dp = fm.sm.dp.get('juniper_srx')
        >>> dp
        juniper_srx
        >>> dp.version
        '1.24.10'
    """

    ep_name = 'plugin'
    collectionConfig = CollectionConfig
    #collectionConfig = JsonField

    def __init__(self, config, app):
        super().__init__(config, app)

        self.name = config['artifactId']
        self.artifacts = [ArtifactFile(f, self.app, self.url) for f in 
                    self.artifacts]

    def _url_create(self):
        """ General self.url create """
        url = '{ep}/{gid}/{aid}'.format(ep=self.ep_url, 
                                        gid=self.groupId,
                                        aid=self.artifactId)
        return url

    def update(self):
        """Nothing to update"""
        raise NotImplementedError(
            "Writes are not supported for this endpoint."
        )

    def save(self):
        raise NotImplementedError(
            "Writes are not supported for this endpoint."
        )

    def layout(self):
        key = 'layout'
        filters = {'layoutName': 'layout.json'}
        req = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        )
        return req.post()

    def get(self, name='dc.zip'):
        """Get the blob (artifact) from Device Pack

        Kwargs:
            name (str): name of the artifact (dc.zip, plugin.jar, etc)

        Return:
            bytes: your blob of stuff
        """
        req = Request(
            base=self.url,
            key=name,
            session=self.session,
        )
        return req.get_content()

    def template(self):
        """ Get default template format for a device.
        
        :..note that a number of fields can take bad information, 
        like empty strings, '', and Secmanager appears to happily
        create devices and things will appear to work. Problems may
        arise on device update calls though where other parts of
        the system fields that should not exist and error out.

        Return:
            dict: template information for a device with defaults included
        """

        resp = self.layout()

        template = {}
        template['name'] = None
        template['description'] = None
        template['managementIp'] = None
        template['domainId'] = self.app.api.domain_id
        # Fix? in later versions we require a Group
        #template['dataCollectorId'] = 1  # Assuming
        #template['collectorGroupId] = ''
        #template['collectorGroupName'] = ''
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

    def __str__(self):
        return str(self.artifactId)


class DevicePacks(Endpoint):
    """Device Packs. There is no API to query individual Device
    Packs to filter thus we retrieve all DPs and query locally.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Examples:
        Get a list of all device packs
        >>> device_packs = fm.sm.dp.all()

        Get a single device pack by artifactId
        >>> dp = fm.sm.dp.get('juniper_srx')

        Get a list of device packs by config options
        >>> fm.sm.dp.filter(ssh=True)
    """
    ep_name = 'plugin'

    def __init__(self, api, app, record=DevicePack):
        super().__init__(api, app, record=DevicePack)

    def all(self):
        """ Get all device packs

        Examples:

        >>> device_packs = fm.sm.dp.all()
        """

        key = 'list/DEVICE_PACK'
        filters = {'sort': 'artifactId',
                   'showHidden': True}
        req = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def get(self, *args, **kwargs):
        """ Query and retrieve individual DevicePack. Spelling matters.

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
            # Only getting exact matches
            id = args[0]
            dp_l = [dp for dp in dp_all if dp.artifactId == id]
            if len(dp_l) == 1:
                return dp_l[0]
            else:
                raise Exception("The requested aritfactId: {} could not "
                                "be found".format(id))
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
            file (bytes): the bytes to send that make a device pack (JAR)

        Returns:
            bool: The return value. True for success upload, False otherwise

        Example:
            >>> dp = fm.sm.dp.get('juniper_srx')
            >>> fn = '/path/to/file/srx.jar'
            >>> with open(fn, 'rb') as f:
            >>>     file = f.read()
            >>> dp.upload(file)

            >>> dp = fm.sm.dp.get('juniper_srx')
            >>> fn = 'srx.jar'
            >>> path = '/path/to/file/srx.jar'
            >>> dp.upload((fn, open(path, 'rb'))
        """
        files = {'devicepack.jar': file}
        filters = {'overwrite': True}

        req = Request(
            base=self.url,
            filters=filters,
            session=self.session,
        )
        return req.post(files=files)

        #url = '{url}/?overwrite=true'.format(url=self.url)
        #self.session.headers.pop('Content-type', None)  # If "content-type" exists get rid.
        #log.debug('POST {}'.format(url))
        #resp = self.session.post(url, files={'devicepack.jar': file})
        #if resp.status_code == 200:
        #    return True
        #else:
        #    raise RequestError(resp)


class ArtifactFile(Record):
    """An Artifact File
    """

    def __init__(self, config, app, ep_url):
        super().__init__(config, app)
        self.url = '{ep}/{name}'.format(ep=ep_url,
                                    name=config['name'])

    def save(self):
        raise NotImplementedError(
            "Writes are not supported for this Record."
        )

    def update(self):
        raise NotImplementedError(
            "Writes are not supported for this Record."
        )

    def delete(self):
        raise NotImplementedError(
            "Writes are not supported for this Record."
        )

    def get(self):
        """Get the raw file
        
        Return:
            bytes: the bytes that make up the file
        """
        req = Request(
            base=self.url,
            session=self.session,
        )
        return req.get_content()

    def __repr__(self):
        return("ArtifactFile<(name='{}')>".format(self.name))

    def __str__(self):
        return("{}".format(self.name))