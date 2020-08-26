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
from urllib.parse import urlparse
import warnings
from typing import Optional

# Third-Party packages
import requests  # performing web requests

# Local packages
from firemon_api.core.query import (Request, 
                                    url_param_builder,
                                    RequestError)
from firemon_api import version
from firemon_api.apps import (GlobalPolicyController,
                              PolicyOptimizer,
                              PolicyPlanner,
                              SecurityManager
                             )
log = logging.getLogger(__name__)


class FiremonAPI(object):
    """ The FiremonAPI object is the entry point to firemon_api

    Instantiate FiremonAPI() with the appropriate named arguments.
    `auth()` then specify which app and endpoint with which to interact.

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
        domain_id (int): the domain.
        proxy (str): ip.add.re.ss:port of proxy

    Valid applications:
        * sm: SecurityManager()
        * gpc: GlobalPolicyController()
        * pp: PolicyPlanner()
        * po: PolicyOptimizer()

    Examples:
        Import the API
        >>> import firemon_api as fmapi
        >>> fm = fmapi.api('redfin-aio').auth('user', 'password')
        >>> fm
        <Firemon(url='https://redfin-aio', version='10.0.0')>

        >>> fm.sm.dp.all()

        >>> fm.sm.devices.all()

        Change working domain
        >>> fm.domain_id = 2

        Set your own requests.Session(). Override other settings here
        if I forgot to set them.
        >>> import requests
        >>> import firemon_api as fmapi
        >>> fm = fmapi.api('gizmo').auth('username', 'password')
        >>> s = requests.Session()
        >>> s.auth = ('foo', 'bar')
        >>> s.verify = False
        >>> fm.session = s
    """

    def __init__(
        self,
        host: str,
        timeout: int = 20,
        verify: Optional = True,
        cert: Optional = None,
        domain_id: int = 1,
        proxy: str = None,
    ):

        self.timeout = timeout
        self.verify = verify
        self.cert = cert

        self.session = requests.Session()
        #self.session.auth = (self.username, self.password)  # Basic auth is used
        self.default_headers = {'User-Agent': 'py-firemon-api/{}'.format(
                                                            version.__version__),
                                'Accept-Encoding': 'gzip, deflate',
                                'Accept': '*/*', 'Connection': 'keep-alive'}
        self.session.headers.update(self.default_headers)
        self.session.verify = self.verify
        self.session.cert = self.cert
        self.session.timeout = self.timeout
        if proxy:
            self.session.proxies = {'http': proxy, 'https': proxy}

        self.host = host
        self.domain_id = domain_id
        self._version = 'unknown'

    def auth(self, username: str, password: str,):
        """User must auth to get access to most api. Basic auth 
        can be set at __init__ and if the u:p is correct access
        to calls goes fine. But if it is not correct it is easy
        to lock out a user.
        """
        log.debug(
            "Authenticating Firemon connection: %s",
            self.host
        )
        self.session.auth = (username, password)
        key = 'securitymanager/api/authentication/login'
        payload = {'username': username, 'password': password}
        Request(
            base=self.base_url,
            key=key,
            session=self.session,
        ).post(json=payload)
        # Update items of interest
        self._version = self._versions()['fmosVersion']
        self._verify_domain(self.domain_id)

        self.sm = SecurityManager(self)
        self.gpc = GlobalPolicyController(self)
        self.po = PolicyOptimizer(self)
        self.pp = PolicyPlanner(self)

    def _versions(self):
        """All the version info from API"""
        key = 'securitymanager/api/version'
        resp = Request(
            base=self.base_url,
            key=key,
            session=self.session,
        ).get()
        return(resp)

    def _verify_domain(self, id):
        """ Verify that requested domain Id exists.
        Set the domain_id that will be used.
        """
        key = "securitymanager/api/domain/{id}".format(id=str(id))
        try:
            resp = Request(
                base=self.base_url,
                key=key,
                session=self.session,
            ).get()
        except RequestError:
            warnings.warn('User does not have access to requested domain calls')
        self.domain_name = resp['name']
        self.domain_description = resp['description']

    def change_password(self, username: str, oldpw: str, newpw: str):
        """Allow change of password without being authed for other
        API calls.

        Args:
            username (str): Username to change password
            oldpw (str): Old password
            newpw (str): New password
        """
        key = 'securitymanager/api/user/password'
        data = {'username': username,
                'oldPassword': oldpw,
                'newPassword': newpw,
                'newPasswordConfirm': newpw}

        headers = {"Content-Type": "application/x-www-form-urlencoded",
                   "Accept": "application/json",
                   "Suppress-Auth-Header": 'true'}

        req = Request(
            base=self.base_url,
            key=key,
            headers=headers,
            session=self.session,
        )
        return req.put(data=data)

    def __repr__(self):
        return ("<Firemon(url='{}', "
            "version='{}')>".format(self._base_url, self.version))

    def __str__(self):
        return self.host

    @property
    def domain_id(self):
        return self._domain

    @domain_id.setter
    def domain_id(self, id):
        self._domain = id

    @property
    def base_url(self):
        return self._base_url

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host
        p_host = urlparse(host)
        if p_host.netloc:
            self._base_url = 'https://{}'.format(p_host.netloc)
        else:
            self._base_url = 'https://{}'.format(host)

    @property
    def version(self):
        """FMOS version"""
        return self._version
