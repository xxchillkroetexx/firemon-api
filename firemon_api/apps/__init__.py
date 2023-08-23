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
from firemon_api.core.api import FiremonAPI
from firemon_api.core.query import Request, RequestResponse
from firemon_api.core.response import Record

from .policyoptimizer import *
from .policyplanner import *
from .securitymanager import *
from .controlpanel import *

log = logging.getLogger(__name__)


class DynamicApi(object):
    """Attempt to dynamically create all the APIs

    Warning:
        Most of the names are not intuitive to what they do.
        Good luck and godspeed.
    """

    def __init__(self, dynamic_api: dict, api: FiremonAPI, app, record=None):
        """
        Args:
            dynamic_api (dict): all the json from `get_api`
        """
        if record:
            self.return_obj = record
        else:
            self.return_obj = Record
        self.api = api
        self.session = api.session
        self.app = app
        self.base_url = api.base_url
        self.app_url = app.app_url
        self.domain_url = app.domain_url
        self.url = None
        for path in dynamic_api["paths"].keys():
            for verb in dynamic_api["paths"][path].keys():
                oid = dynamic_api["paths"][path][verb]["operationId"]
                _method = self._make_method(path, verb)
                setattr(self, oid, _method)

    def _make_method(self, path: str, verb: str) -> function:
        if verb == "get":

            def _method(filters=None, add_params=None, **kwargs):
                p = path.lstrip("/")
                key = p.format(**kwargs)
                filters = filters
                req = Request(
                    base=self.app_url,
                    key=key,
                    filters=filters,
                    session=self.session,
                )
                return req.get(add_params=add_params)

            return _method

        elif verb == "put":

            def _method(filters=None, data=None, **kwargs):
                p = path.lstrip("/")
                key = p.format(**kwargs)
                filters = filters
                req = Request(
                    base=self.app_url,
                    key=key,
                    filters=filters,
                    session=self.session,
                )
                return req.put(data=data)

            return _method

        elif verb == "post":

            def _method(filters=None, data=None, files=None, **kwargs):
                p = path.lstrip("/")
                key = p.format(**kwargs)
                filters = filters
                req = Request(
                    base=self.app_url,
                    key=key,
                    filters=filters,
                    session=self.session,
                )
                return req.post()

            return _method

        elif verb == "delete":

            def _method(filters=None, **kwargs):
                p = path.lstrip("/")
                key = p.format(**kwargs)
                filters = filters
                req = Request(
                    base=self.app_url,
                    key=key,
                    filters=filters,
                    session=self.session,
                )
                return req.delete()

            return _method


class App(object):
    """Base class for Firemon Apps"""

    name = None

    def __init__(self, api: FiremonAPI):
        self.api = api
        self.session = api.session
        self.base_url = api.base_url
        self.app_url = f"{api.base_url}/{self.__class__.name}/api"
        self.domain_url = f"{self.app_url}/domain/{str(self.api.domain_id)}"

    def set_api(self) -> RequestResponse:
        """Attempt to auto create all api calls by reading
        the dynamic api endpoint make a best guess. User must
        be authorized to read api documentation to use this.

        All auto created methods get setattr on `exec` for `App`.
        """
        _dynamic_api = self.get_api()
        setattr(self, "exec", DynamicApi(_dynamic_api, self.api, self))

    def get_api(self) -> RequestResponse:
        """Return API specs from the dynamic documentation"""

        key = "openapi.json"
        req = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        )
        return req.get()

    def __repr__(self):
        return f"<App({self.name})>"

    def __str__(self):
        return f"{self.name}"


class SecurityManager(App):
    """Represents Security Manager in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * centralsyslogs: CentralSyslogs()
        * collectionconfigs: CollectionConfigs()
        * collectors: Collectors()
        * collectorgroups: CollectorGroups()
        * devices: Devices()
        * dp: DevicePacks()
        * revisions: Revisions()
        * users: Users()
        * Todo: add more as needed
    """

    name = "securitymanager"

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        self.centralsyslogconfigs = CentralSyslogConfigs(self.api, self)
        self.centralsyslogs = CentralSyslogs(self.api, self)
        self.collectionconfigs = CollectionConfigs(self.api, self)
        self.collectors = Collectors(self.api, self)
        self.collectorgroups = CollectorGroups(self.api, self)
        self.deviceclusters = DeviceClusters(self.api, self)
        self.devices = Devices(self.api, self)
        self.dp = DevicePacks(self.api, self)  # Todo: create the other /plugin
        self.es = ElasticSearch(self.api, self)
        self.license = License(self.api, self)
        self.logging = Logging(self.api, self)
        self.maps = Maps(self.api, self)
        self.revisions = Revisions(self.api, self)
        self.users = Users(self.api, self)
        self.usergroups = UserGroups(self.api, self)
        self.routes = Routes(self.api, self)
        self.siql = Siql(self.api, self)
        self.zones = Zones(self.api, self)
        self.fmzones = FmZones(self.api, self)


class Orchestration(App):
    """Represents Orchestration in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    name = "orchestration"

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        # self.xx = EndPoint(self)


class PolicyOptimizer(App):
    """Represents Policy Optimizer in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    name = "policyoptimizer"

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        # self.xx = EndPoint(self)


class PolicyPlanner(App):
    """Represents Policy Planner in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    name = "policyplanner"

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        self.siql = SiqlPP(self.api, self)
        self.tasks = Tasks(self.api, self)
        self.workflows = Workflows(self.api, self)


class ControlPanel(App):
    """Represents Control Panel in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * ca: EndPoint()
        * cleanup: EndPoint()
        * config: EndPoint()
        * db: EndPoint()
        * diagpkg: EndPoint()
    """

    def __init__(self, api):
        super().__init__(api)
        self.domain_url = None
        if self.api._cpl_proxy:
            self.app_url = f"{api.base_url}/__fmos-cpl__/api"
        else:
            self.app_url = f"{api.base_url}:55555/api"

        # Endpoints
        self.ca = CertAuth(self.api, self)
        self.cleanup = Cleanup(self.api, self)
        self.config = Config(self.api, self)
        self.db = Database(self.api, self)
        self.diagpkg = DiagPkg(self.api, self)

    def set_api(self, _: Never) -> None:
        """Maybe later"""
        raise NotImplementedError("Maybe some other time")

    def get_api(self) -> RequestResponse:
        """Return API specs if the 5555 port is up."""

        key = "api-doc"
        try:
            req = Request(
                base=f"{self.base_url}:55555",
                key=key,
                session=self.session,
            )
            return req.get()
        except:
            raise NotImplementedError("No access to api-doc endpoint")

    def email_confirm(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        code=None,
        k: Optional[str] = None,
    ) -> RequestResponse:
        """
        Kwargs:
            k (str)
            username (str)
        """

        key = "emailconfirm"
        headers = {"Content-Type: application/x-www-form-urlencoded"}

        filters = {"k": k, "username ": username, "email": email, "code": code}

        r = Request(
            base=self.app_url,
            headers=headers,
            key=key,
            filters=filters,
            session=self.session,
        ).post()
        return r

    def email_confirm_resend(self, username: str) -> RequestResponse:
        key = "resendemailconfirm"
        filters = {"username ": username}
        r = Request(
            base=self.app_url,
            key=key,
            filters=filters,
            session=self.session,
        ).post()
        return r

    def get_session(self) -> RequestResponse:
        key = "session"
        r = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        ).get()
        return r

    def health(
        self, checks: str = "default", cache: str = "default"
    ) -> RequestResponse:
        """verbose state and health info

        Kwargs:
            checks (str): default, detailed, full
            cache (str): default, ignore, only
        """
        filters = {"cache": f"{cache}"}
        key = f"health/{checks}"
        r = Request(
            base=self.app_url,
            key=key,
            filters=filters,
            session=self.session,
        ).get()
        return r

    def info(self) -> RequestResponse:
        key = "info"
        r = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        ).get()
        return r

    def perf(self) -> RequestResponse:
        key = "perf"
        r = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        ).get()
        return r

    def state(self) -> RequestResponse:
        key = "state"
        r = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        ).get()
        return r

    def user_update(self, config: dict) -> RequestResponse:
        """update user info

        Args:
            config (dict)
        """

        key = "user"

        r = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        ).put(json=config)

        return r
