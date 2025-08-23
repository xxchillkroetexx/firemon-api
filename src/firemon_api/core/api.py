# Standard packages
import logging
import socket
import warnings

from urllib.parse import urlparse
from typing import Optional

# Third-Party packages
import requests  # performing web requests

# Local packages
import firemon_api
from firemon_api.core.query import (
    Request,
    RequestError,
    RequestResponse,
)

log = logging.getLogger(__name__)


class FiremonAPI(object):
    """The FiremonAPI object is the entry point to firemon_api

    Instantiate FiremonAPI() with the appropriate named arguments.
    `auth()` then specify which app and endpoint with which to interact.

    Parameters:
        host (str): host or IP.
        username (str): Firemon web username
        password (str): Firemon web password

    Keyword Arguments:
        timeout (int): timeout value for Requests Session(). (default: 20)
        verify (optional): Requests verify ssl cert (bool) or a path (str) to PEM certificate. (default: ``True``)
        cert (optional): if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair. ex: openssl x509 -in <(openssl s_client -connect {SERVER}:{PORT} -prexit 2>/dev/null) > {SERVER}.pem
        domain_id (int): the domain.
        proxy (str): ip.add.re.ss:port of proxy

    Attributes:
        sm: SecurityManager() application
        orch: Orchestration() application
        pp: PolicyPlanner() application
        po: PolicyOptimizer() application
        cpl: ControlPanel() application

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

        Set your own requests.Session(). Override other settings here if I forgot to set them.

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
        verify: bool = True,
        cert: Optional[str] = None,
        domain_id: int = 1,
        proxy: str = None,
    ):
        self.timeout = timeout
        self.verify = verify
        self.cert = cert

        self.session = requests.Session()
        # self.session.auth = (self.username, self.password)  # Basic auth is used
        self.default_headers = {
            "User-Agent": f"py-firemon-api/{firemon_api.__version__}",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }
        self.session.headers.update(self.default_headers)
        self.session.verify = self.verify
        self.session.cert = self.cert
        self.session.timeout = self.timeout
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

        self.host = host
        self.domain_id = domain_id
        self._version = "unknown"
        self._version_fmos = "unknown"
        self._version_platform = "unknown"

    def auth(self, username: str, password: str):
        """User must auth to get access to most api. Basic auth
        can be set at __init__ and if the u:p is correct access
        to calls goes fine. But if it is not correct it is easy
        to lock out a user.

        Parameters:
            username (str): FireMon username
            password (str): password associated to username
        """
        log.info(f"Authenticating Firemon connection: {self.host}")
        self.session.auth = (username, password)
        self.username = username
        key = "securitymanager/api/authentication/login"
        payload = {"username": username, "password": password}
        Request(
            base=self.base_url,
            key=key,
            session=self.session,
        ).post(json=payload)
        # Get and set the token? Basic Auth is easy and doesn not have timeout issues
        # self.token = resp["token"]
        # self.session.headers.update({"X-FM-AUTH-Token": self.token})

        # Update items of interest
        versions = self._versions()
        self._version = versions["version"]
        self._version_fmos = versions["fmosVersion"]
        self._version_platform = versions["platformVersion"]
        self._verify_domain(self.domain_id)

        from firemon_api.apps import (
            Orchestration,
            PolicyOptimizer,
            PolicyPlanner,
            SecurityManager,
        )

        self.sm = SecurityManager(self)
        self.orch = Orchestration(self)
        self.po = PolicyOptimizer(self)
        self.pp = PolicyPlanner(self)
        return self

    def auth_cpl(self, username: str, password: str, cpl_proxy=False):
        """Control Panel that is normally accessed via 55555

        Parameters:
            username (str): FMOS level username
            password (str): FMOS level password associated to user

        Keyword Arguments:
            cpl_proxy (bool): default: Fasle
        """
        log.info(f"Authenticating Firemon Control Panel: {self.host}")
        self._cpl_proxy = cpl_proxy
        self._cpl_cookies = requests.cookies.RequestsCookieJar()
        key = "api/login"
        if cpl_proxy:
            url = f"{self.base_url}/__fmos-cpl__"
        else:
            url = f"{self.base_url}:55555"
        payload = {"username": username, "password": password}
        r = Request(
            base=url,
            key=key,
            session=self.session,
        ).post_cpl_auth(data=payload)
        self._cpl_cookies = r.cookies
        log.debug(r.json())

        from firemon_api.apps import ControlPanel

        self.cpl = ControlPanel(self)
        return self

    def _versions(self) -> RequestResponse:
        """All the version info from API"""
        key = "securitymanager/api/version"
        resp = Request(
            base=self.base_url,
            key=key,
            session=self.session,
        ).get()
        return resp

    def _verify_domain(self, id: int) -> None:
        """Verify that requested domain Id exists.
        Set the domain_id that will be used.
        """
        key = f"securitymanager/api/domain/{str(id)}"
        try:
            resp = Request(
                base=self.base_url,
                key=key,
                session=self.session,
            ).get()
            self.domain_name = resp["name"]
            self.domain_description = resp["description"]
        except RequestError:
            warnings.warn("User does not have access to requested domain calls")

    def change_password(self, username: str, oldpw: str, newpw: str) -> RequestResponse:
        """Allow change of SecMgr password without being authed for other
        API calls.

        Parameters:
            username (str): Username to change password
            oldpw (str): Old password
            newpw (str): New password

        Returns:
            bool
        """
        key = "securitymanager/api/user/password"
        data = {
            "username": username,
            "oldPassword": oldpw,
            "newPassword": newpw,
            "newPasswordConfirm": newpw,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Suppress-Auth-Header": "true",
        }

        req = Request(
            base=self.base_url,
            key=key,
            headers=headers,
            session=self.session,
        )
        return req.put(data=data)

    def __repr__(self):
        return f"<Firemon(url={self._base_url}, version={self.version})>"

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
        p_host = urlparse(host)
        if p_host.netloc:
            self._host = p_host.netloc.split(":")[0]
            self._base_url = f"{p_host.scheme}://{p_host.netloc}"
        else:
            self._host = host           
            self._base_url = f"https://{host}"
        try:
            socket.gethostbyname(self._host)
        except socket.gaierror:
            warnings.warn(f"Host {self._host} does not resolve.")

    @property
    def version(self):
        return self._version

    @property
    def version_fmos(self):
        return self._version_fmos

    @property
    def version_platform(self):
        return self._version_platform
