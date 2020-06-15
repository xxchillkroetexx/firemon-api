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


class CollectionConfig(Record):
    """Collection Configuration Record

    Args:
        config (dict): dictionary of things values from json
        endpoint (obj): Endpoint()

    Examples:
        Get a list of all Collection Configs
        >>> fm.sm.cc.all()
        [4, 36, 18, 38, 24, ...]

        Get a Collection Config by ID
        >>> cc = fm.sm.cc.get(47)

        Set a Device by ID to the Collection Config
        >>> cc.device_set(21)
        True

        Set this CC as the default for associate Device Pack
        >>> cc.devicepack_set()
        True
    """
    ep_name = 'collectionconfig'

    def __init__(self, config, app):
        super().__init__(config, app,)

        self.no_no_keys = ['index',
			               'createdBy',
			               'createdDate',
			               'lastModifiedBy',
			               'lastModifiedDate'
			               ]

    def devicepack_set(self) -> bool:
        """ Set CollectionConfig for Device Pack assignment. """
        key = 'devicepack/{devicepack_id}/assignment/{id}'.format(
                                            devicepack_id=self.devicePackId,
                                            id=self.id)
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.put(None)

    def devicepack_unset(self) -> bool:
        """ Unset CollectionConfig for Device Pack assignment.
        Effectively sets back to 'default'
        """
        key = 'devicepack/{devicepack_id}/assignment'.format(
                                            devicepack_id=self.devicePackId)
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.delete()

    def device_set(self, id) -> bool:
        """ Set CollectionConfig for a device by ID. If requested 
        device IDs device pack does not match CC device pack server
        handles mismatch and will NOT set. If device ID is not 
        found server handles mismatch and will NOT set.

        Args:
            id (int): The ID for the device as understood by Firemon

        Return:
            bool: True if device set
        """
        key = 'device/{device_id}/assignment/{id}'.format(
                                                    device_id=id,
                                                    id=self.id)
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.put(None)

    def device_unset(self, id) -> bool:
        """ Unset a device from CollectionConfig

        Args:
            id (int): The ID for the device as understood by Firemon

        Return:
            bool: True if device unset
        """
        key = 'device/{device_id}/assignment'.format(
                                                device_id=id)
        req = Request(
            base=self.url,
            key=key,
            session=self.
            session,
        )
        return req.delete()

    def __repr__(self):
        return("<CollectionConfig(id='{}', name='{}')>".format(
                                                        self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))


class CollectionConfigs(Endpoint):
    """Collection Configs Endpoint

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
        devicepack_id (int): Device Pack id
        device_id (int): Device id

    Examples:
        >>> cc = fm.sm.cc.get(46)
        >>> cc = fm.sm.cc.filter(
                activatedForDevicePack=True,
                devicePackArtifactId='juniper_srx')[0]
    """

    ep_name = 'collectionconfig'

    def __init__(self, api, app, 
                record=CollectionConfig,
                device_id: int=None,
                devicepack_id: int=None):
        super().__init__(api, app, record=CollectionConfig)
        
        self._device_id = device_id
        self._devicepack_id = devicepack_id

    def all(self):
        """Get all `Record` """
        filters = None
        if self.device_id:
            filters = {'devicePackId': self.devicepack_id}

        req = Request(
            base=self.url,
            filters=filters,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def filter(self, *args, **kwargs):
        """ Retrieve a filterd list of CollectionConfigs
        Note: review the dictionary for all keywords
        Args:
            **kwargs: key value pairs in a collectionconfig dictionary
        Return:
            list: a list of CollectionConfig(object)
        Examples:
            >>> fm.sm.cc.filter(devicePackArtifactId='juniper_srx')
            [47, 21, 46]
            >>> fm.sm.cc.filter(activatedForDevicePack=True, devicePackId=3)
            [<CollectionConfig(id='1', name='default')>]
            >>> fm.sm.cc.filter(devicePackDeviceType='FIREWALL')
            [4, 24, 13, 8, 30, 31, 3, 5, ...]
            >>> fm.sm.cc.filter(activatedForDevicePack=True)
            [4, 36, 18, 38, 24, 13, 8, 30, ...]
        """
        cc_all = self.all()
        if args:
            kwargs.update({'name': args[0]})

        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [cc for cc in cc_all if kwargs.items() <= dict(cc).items()]

    def count(self):
        return len(self.all())

    @property
    def device_id(self):
        return self._device_id

    @property
    def devicepack_id(self):
        return self._devicepack_id