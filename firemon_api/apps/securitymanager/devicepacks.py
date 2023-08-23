"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import logging
from typing import Never, Optional

# Local packages
from firemon_api.apps import SecurityManager
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request, RequestResponse, RequestError
from firemon_api.core.utils import _find_dicts_with_key
from .collectionconfigs import CollectionConfig

log = logging.getLogger(__name__)


class DevicePack(Record):
    """Representation of the device pack

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

    _ep_name = "plugin"
    collectionConfig = CollectionConfig
    # collectionConfig = JsonField

    def __init__(self, config: dict, app: SecurityManager):
        super().__init__(config, app)

        self.name = config["artifactId"]
        self.artifacts = [ArtifactFile(f, self._app, self._url) for f in self.artifacts]

    def _url_create(self) -> str:
        """General self.url create"""
        url = f"{self._ep_url}/{self.groupId}/{self.artifactId}"
        return url

    def update(self, _: Never) -> None:
        """Nothing to update"""
        raise NotImplementedError("Writes are not supported for this endpoint.")

    def save(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported for this endpoint.")

    def layout(self) -> RequestResponse:
        key = "layout"
        filters = {"layoutName": "layout.json"}
        req = Request(
            base=self._url,
            key=key,
            filters=filters,
            session=self._session,
        )
        return req.post()

    def get(self, name="dc.zip") -> RequestResponse:
        """Get the blob (artifact) from Device Pack

        Kwargs:
            name (str): name of the artifact (dc.zip, plugin.jar, etc)

        Return:
            bytes: your blob of stuff
        """
        req = Request(
            base=self._url,
            key=name,
            session=self._session,
        )
        return req.get_content()

    def template(self) -> dict:
        """Get default template format for a device.

        :..note that a number of fields can take bad information,
        like empty strings, '', and Secmanager appears to happily
        create devices and things will appear to work. Problems may
        arise on device update calls though where other parts of
        the system fields that should not exist and error out.

        Return:
            dict: template information for a device with defaults included
        """

        template = {}
        template["name"] = None
        template["description"] = None
        template["managementIp"] = None
        template["domainId"] = self._app.api.domain_id  # set and verified in API
        # Fix? in later versions we require a Group
        # template['dataCollectorId'] = 1  # Assuming
        # template['collectorGroupId] = ''
        # template['collectorGroupName'] = ''
        template["devicePack"] = {}
        template["devicePack"]["artifactId"] = self.artifactId
        template["devicePack"]["deviceName"] = self.deviceName
        template["devicePack"]["groupId"] = self.groupId
        template["devicePack"]["id"] = self.id
        template["devicePack"]["type"] = self.type
        template["devicePack"]["deviceType"] = self.deviceType
        template["devicePack"]["version"] = self.version
        template["extendedSettingsJson"] = {}

        try:
            # We have 'devices' that are not devices which no longer have layout.json files
            resp = self.layout()
        except RequestError:
            log.debug(f"No layout.json for {self.artifactId}.")
            return template

        for response in _find_dicts_with_key("key", resp):
            # Get rid of headings that are capitalized
            # hopefully all Json name format is followed
            if response["key"][0].isupper():
                continue
            # apparently we are serializing values `key.subkey` "interestingly".
            #   unsure if this is an Angular thing. Told that max of 1 key deep?
            key = None
            sub_key = None
            k_s = response["key"].split(".", maxsplit=1)
            if len(k_s) == 1:
                key = response["key"]
                template["extendedSettingsJson"].setdefault(key)
            else:
                key = k_s[0]
                sub_key = k_s[1]
                template["extendedSettingsJson"].setdefault(key, {}).setdefault(sub_key)
            if "defaultValue" in response and not sub_key:
                template["extendedSettingsJson"][key] = response["defaultValue"]
            elif "defaultValue" in response:
                template["extendedSettingsJson"][key][sub_key] = response[
                    "defaultValue"
                ]
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

    ep_name = "plugin"

    def __init__(self, api: FiremonAPI, app: SecurityManager, record=DevicePack):
        super().__init__(api, app, record=record)

    def all(self) -> list[DevicePack]:
        """Get all device packs

        Examples:

        >>> device_packs = fm.sm.dp.all()
        """

        key = "list/DEVICE_PACK"
        filters = {"sort": "artifactId", "showHidden": True}
        req = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def get(self, *args, **kwargs) -> Optional[DevicePack]:
        """Query and retrieve individual DevicePack. Spelling matters.

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
                raise Exception(f"The requested aritfactId: {id} could not be found")
        except IndexError:
            id = None

        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result."
                        "Check the kwarg(s) passed are valid or"
                        "use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        """Retrieve a filtered list of DevicePacks

        Args:
            **kwargs: key value pairs in a device pack dictionary

        Return:
            list: a list of DevicePack(object)

        Examples:

        >>> fm.sm.dp.filter(ssh=True)
        """

        if not kwargs:
            raise ValueError("filter must have kwargs")

        dp_all = self.all()

        return [dp for dp in dp_all if kwargs.items() <= dict(dp).items()]

    def upload(self, file: bytes):
        """Upload device pack

        Args:
            file (bytes): the bytes to send that make a device pack (JAR)

        Returns:
            bool: The return value. True for success upload, False otherwise

        Example:
            >>> fn = '/path/to/file/srx.jar'
            >>> with open(fn, 'rb') as f:
            >>>     file = f.read()
            >>> fm.sm.dp.upload(file)

            >>> fn = 'srx.jar'
            >>> path = '/path/to/file/srx.jar'
            >>> fm.sm.dp.upload((fn, open(path, 'rb'))
        """
        files = {"devicepack.jar": file}
        filters = {"overwrite": True}

        req = Request(
            base=self.url,
            filters=filters,
            session=self.session,
        )
        return req.post(files=files)

        # url = '{url}/?overwrite=true'.format(url=self.url)
        # self.session.headers.pop('Content-type', None)  # If "content-type" exists get rid.
        # log.debug('POST {}'.format(url))
        # resp = self.session.post(url, files={'devicepack.jar': file})
        # if resp.status_code == 200:
        #    return True
        # else:
        #    raise RequestError(resp)


class ArtifactFile(Record):
    """An Artifact File"""

    def __init__(self, config, app, ep_url):
        super().__init__(config, app)
        self._url = f"{ep_url}/{config['name']}"

    def save(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def update(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def delete(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def get(self):
        """Get the raw file

        Return:
            bytes: the bytes that make up the file
        """
        req = Request(
            base=self._url,
            session=self._session,
        )
        return req.get_content()
