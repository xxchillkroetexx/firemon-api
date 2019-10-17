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

# Third-Party packages
import requests  # performing web requests
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass

# Local packages
from fmapi.errors import AuthenticationError, FiremonError, LicenseError
from fmapi.errors import DeviceError, DevicePackError, VersionError
from fmapi.apps.securitymanager import SecurityManager
from fmapi.apps.globalpolicycontroller import GlobalPolicyController
from fmapi.apps.policyplanner import PolicyPlanner
from fmapi.apps.policyoptimizer import PolicyOptimizer


class FiremonAPI(object):
    """ The FiremonAPI object is the entry point to fmapi

    Instantiate FiremonAPI() with the appropriate named arguments then
    specify which app and endpoint with which to interact.

    Args:
        host (str): host or IP.
        username (str): Firemon web username
        password (str): Firemon web password

    Kwargs:
        timeout (int): timeout value for Requests Session(). (default: 20)
        verify_ssl (bool): Requests verify ssl cert. (default: False)
        domainId (int): the domain.
        proxy (str): ip.add.re.ss:port of proxy

    Valid attributes currently are (see domainId setter for updates):
        * sm: SecurityManager()
        * gpc: GlobalPolicyController()
        * pp: PolicyPlanner()
        * po: PolicyOptimizer()

    Examples:
        Import the API
        >>> import fmapi
        >>> fm = fmapi.api('hobbes', 'firemon', 'firemon')
        >>> fm
        Firemon: hobbes ver. 8.24.1

        >>> fm.sm.dp.all()

        >>> fm.sm.devices.all()

        Change working domain
        >>> fm.domainId = 2
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        timeout: int = 20,
        verify_ssl: bool = False,
        domainId: int = 1,
        proxy: str = None,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        self.session.auth = (self.username, self.password)  # Basic auth is used
        self.default_headers = {'User-Agent': 'dev-netsec/0.0.1',
                                'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*',
                                'Connection': 'keep-alive'}
        self.session.headers.update(self.default_headers)
        self.session.verify = self.verify_ssl  # It'd be nice to default to True. Currently defeat purpose of SSL
        self.session.timeout = self.timeout
        if proxy:
            self.session.proxies = {'http': proxy, 'https': proxy}
        self._auth()

        # Much of all the APIs requires a domain ID. There is also a fair amount
        #   that does not require a Domain ID. There may be a better way to
        #   code this but this appears good enough. What all the endpoints then
        #   are instantiated in the domainId setter.
        self.domainId = domainId

        # This is expecting that FMOS major version 9 will move devpacks majors
        self._major_to_pack = { '8': '1',
                                '9': '2',
                              }

    def _auth(self):
        """ Initial check for access and version information """
        url = self._base_url + '/securitymanager/api/authentication/login'
        payload = {'username': self.username, 'password': self.password}
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.post(url, data=json.dumps(payload))
        if (response.status_code != 200):
            raise AuthenticationError("HTTP code: {}  Server response: "
                                      " {}".format(str(response.status_code), response.text))
        else:
            self.version = self._get_version()
            self.major_version = self.version.split('.')[0]
            self.minor_version = self.version.split('.')[1]
            self.micro_version = self.version.split('.')[2]

    def _get_version(self) -> dict:
        """ Retrieve fmos version for display and filter device packs """
        url = self._base_url + '/securitymanager/api/version'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()['fmosVersion']
        else:
            raise FiremonError("ERROR retrieving FMOS version! HTTP code: {}  "
                              "Server response: {}".format(
                              response.status_code, response.text))

    def _verify_domain(self, id):
        """ Verify that requested domain Id exists.
        Set the domainId that will be used.
        """
        url = self.base_url + "/securitymanager/api/domain/{id}".format(id=str(id))
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            self.domainName = resp['name']
            self.domainDescription = resp['description']
            return True
        else:
            return False

    def __repr__(self):
        return("<Firemon(host='{}', version='{}')>".format(self.host, self.version))

    def __str__(self):
        return("FMOS: {} ver. {}".format(self.host, self.version))

    @property
    def domainId(self):
        return self._domain

    @domainId.setter
    def domainId(self, id):
        if self._verify_domain(id):
            self._domain = id
            self.sm = SecurityManager(self)
            self.gpc = GlobalPolicyController(self)
            self.po = PolicyOptimizer(self) # Todo: build this
            self.pp = PolicyPlanner(self) # Todo: build this
        else:
            raise FiremonError('Domain {} is not valid'.format(id))

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, host):
        self._base_url = 'https://' + host

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host
        self.base_url = self._host
