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
from fmapi.errors import AuthenticationError, FiremonError, LicenseError
from fmapi.errors import DeviceError, DevicePackError, VersionError
from .centralsyslogs import CentralSyslogs, CentralSyslog
from .collectionconfigs import CollectionConfigs, CollectionConfig
from .collectors import Collectors, DataCollector
from .devicepacks import DevicePacks, DevicePack
from .devices import Devices, Device
from .revisions import Revisions, Revision, ParsedRevision
from .users import Users, User, UserGroup


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
        self.domain_url = self.sm_url + "/domain/{id}".format(id=str(self.api.domainId))

        #self._verify_domain(self.api.domainId)

        # Endpoints
        self.cc = CollectionConfigs(self)
        self.centralsyslogs = CentralSyslogs(self)
        self.collectors = Collectors(self)
        self.devices = Devices(self)
        self.dp = DevicePacks(self)  # Todo: create the other /plugins
        self.revisions = Revisions(self)
        self.users = Users(self)

    def es_reindex(self):
        """ Mark Elastic Search for reindex """
        url = self.sm_url + '/es/reindex'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.post(self.url)
        if response.status_code == 204:
            return True
        else:
            return False

    def __repr__(self):
        return("<Security Manager(url='{}')>".format(self.sm_url))

    def __str__(self):
        return('{}'.format(self.sm_url))
