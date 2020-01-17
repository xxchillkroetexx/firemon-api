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
from firemon_api.errors import (
    AuthenticationError, FiremonError, LicenseError,
    DeviceError, DevicePackError, VersionError
)


class GlobalPolicyController(object):
    """ Represents Global Policy Controller in Firemon

    Args:
        api (obj): FiremonAPI()

    Valid attributes are:
        * xx: EndPoint()
    """

    def __init__(self, api):
        self.api = api
        self.session = api.session
        self.gpc_url = "{url}/globalpolicycontroller/api".format(url=api.base_url)
        self.domain_url = self.gpc_url + "/domain/{id}".format(id=str(self.api.domainId))

        # Endpoints
        #self.xx = EndPoint(self)

    def __repr__(self):
        return("<Global Policy Controller(url='{}')>".format(self.gpc_url))

    def __str__(self):
        return('{}'.format(self.gpc_url))
