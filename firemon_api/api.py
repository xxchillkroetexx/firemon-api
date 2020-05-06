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
from typing import Optional
import warnings

# Third-Party packages
import requests  # performing web requests

# Local packages
from firemon_api.errors import (
    AuthenticationError, FiremonError, LicenseError,
    DeviceError, DevicePackError, VersionError,
    FiremonWarning, AuthenticationWarning
)
from firemon_api.apps.securitymanager import SecurityManager
from firemon_api.apps.globalpolicycontroller import GlobalPolicyController
from firemon_api.apps.policyplanner import PolicyPlanner
from firemon_api.apps.policyoptimizer import PolicyOptimizer

log = logging.getLogger(__name__)

class FiremonAPI(object):
    """ The FiremonAPI object is the entry point to firemon_api

    Instantiate FiremonAPI() with the appropriate named arguments then
    specify which app and endpoint with which to interact.

    Args:
        host (str): host or IP.
        username (str): Firemon web username
        password (str): Firemon web password

    Kwargs:
        timeout (int): timeout value for Requests Session(). (default: 20)
        verify (optional): Requests verify ssl cert (bool) or a path (str) to
            PEM certificate. (default: ``True``)
            hint: get the cert for fmos instance or append it to the CA bundle.
            -----BEGIN CERTIFICATE-----
            <base64>
            -----END CERTIFICATE-----
            ex: export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        cert (optional): if String, path to ssl client cert file (.pem).
            If Tuple, ('cert', 'key') pair.
            ex: openssl x509 -in <(openssl s_client -connect {SERVER}:{PORT} \
                -prexit 2>/dev/null) > {SERVER}.pem
        domainId (int): the domain.
        proxy (str): ip.add.re.ss:port of proxy

    Valid attributes currently are (see domainId setter for updates):
        * sm: SecurityManager()
        * gpc: GlobalPolicyController()
        * pp: PolicyPlanner()
        * po: PolicyOptimizer()

    Examples:
        Import the API
        >>> import firemon_api as fmapi
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
        verify: Optional = True,
        cert: Optional = None,
        domainId: int = 1,
        proxy: str = None,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify = verify
        self.cert = cert

        self.session = requests.Session()
        self.session.auth = (self.username, self.password)  # Basic auth is used
        self.default_headers = {'User-Agent': 'dev-netsec/0.0.1',
                                'Accept-Encoding': 'gzip, deflate',
                                'Accept': '*/*',
                                'Connection': 'keep-alive'}
        self.session.headers.update(self.default_headers)
        self.session.verify = self.verify
        self.session.cert = self.cert
        self.session.timeout = self.timeout
        if proxy:
            self.session.proxies = {'http': proxy, 'https': proxy}
        self._auth()

        # Much of all the APIs requires a domain ID. There is also a fair amount
        #   that does not require a Domain ID. There may be a better way to
        #   code this but this appears good enough. What all the endpoints then
        #   are instantiated in the domainId setter.
        self.domainId = domainId

        # This translates the major release to the dev pack major.
        self._major_to_pack = { '8': '1',
                                '9': '9',
                              }

    def _auth(self):
        """ Initial check for access and version information """
        log.debug(
            "Authenticating Firemon connection: %s",
            self.host
        )
        url = self._base_url + '/securitymanager/api/authentication/login'
        payload = {'username': self.username, 'password': self.password}
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('POST {}'.format(url))
        response = self.session.post(url,
                                    data=json.dumps(payload),
                                    verify=self.verify,
                                    cert=self.cert)
        if (response.status_code != 200):
            raise AuthenticationError("HTTP code: {}  Server response: "
                                      " {}".format(str(response.status_code),
                                      response.text))
        else:
            self.version = self._get_version()
            self.major_version = self.version.split('.')[0]
            self.minor_version = self.version.split('.')[1]
            self.micro_version = self.version.split('.')[2]

    def _get_version(self) -> dict:
        """ Retrieve fmos version for display and filter device packs """
        url = self._base_url + '/securitymanager/api/version'
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('GET {}'.format(url))
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
        url = self.base_url + "/securitymanager/api/domain/{id}".format(
                                                                    id=str(id))
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('GET {}'.format(url))
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            self.domainName = resp['name']
            self.domainDescription = resp['description']
            return True
        elif response.status_code == 403:
            warnings.warn('User is not authorized for request. '
                          'Unable to verify Domain {} exists'.format(id),
                          AuthenticationWarning)
            return False
        else:
            warnings.warn('Unable to verify Domain {} exists'.format(id),
                          FiremonWarning)
            return False

    def __repr__(self):
        return("<Firemon(host='{}', "
            "version='{}')>".format(self.host, self.version))

    def __str__(self):
        return("FMOS: {} ver. {}".format(self.host, self.version))

    @property
    def domainId(self):
        return self._domain

    @domainId.setter
    def domainId(self, id):
        self._verify_domain(id)  # User may not be authorized to validate domain.
        self._domain = id  # Set domain regardless and pop a warning if unable to validate
        self.sm = SecurityManager(self)
        self.gpc = GlobalPolicyController(self)
        self.po = PolicyOptimizer(self) # Todo: build this
        self.pp = PolicyPlanner(self) # Todo: build this

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
