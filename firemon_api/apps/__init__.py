# Standard packages
import logging
from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.query import Request, RequestResponse

log = logging.getLogger(__name__)


from .orchestration import *
from .policyoptimizer import *
from .policyplanner import *
from .securitymanager import *
from .controlpanel import *


class SecurityManager(App):
    """Represents Security Manager in Firemon

    Parameters:
        api (obj): FiremonAPI()
        name (str): name of the application

    Attributes:
        * centralsyslogconfigs: CentralSyslogConfigs()
        * centralsyslogs: CentralSyslogs()
        * collectionconfigs: CollectionConfigs()
        * collectors: Collectors()
        * collectorgroups: CollectorGroups()
        * deviceclusters: DeviceClusters()
        * devices: Devices()
        * dp: DevicePacks()
        * es: ElasticSearch()
        * license: License()
        * logging: Logging()
        * maps: Maps()
        * revisions: Revisions()
        * users: Users()
        * usergroups: UserGroups()
        * routes: Routes()
        * siql: Siql()
        * zones: Zones()
        * fmzones: FmZones()
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
        self.devicegroups = DeviceGroups(self.api, self)
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

    Parameters:
        api (obj): FiremonAPI()
        name (str): name of the application

    Attributes:
        * changes: Changes()
    """

    name = "orchestration"

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        self.changes = Changes(self.api, self)


class PolicyOptimizer(App):
    """Represents Policy Optimizer in Firemon

    Parameters:
        api (obj): FiremonAPI()
        name (str): name of the application

    Attributes:
        * xx: EndPoint()
    """

    name = "policyoptimizer"

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        # self.xx = EndPoint(self.api, self)


class PolicyPlanner(App):
    """Represents Policy Planner in Firemon

    Parameters:
        api (obj): FiremonAPI()
        name (str): name of the application

    Attributes:
        * siql: SiqlPP()
        * tasks: Tasks()
        * workflows: Workflows()
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

    Parameters:
        api (obj): FiremonAPI()
        name (str): name of the application

    Attributes:
        * ca: CertAuth()
        * cleanup: Cleanup()
        * config: Config()
        * db: Database()
        * diagpkg: DiagPkg()
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

    def set_api(self) -> None:
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
        Keyword Arguments:
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

        Keyword Arguments:
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

        Parameters:
            config (dict)
        """

        key = "user"

        r = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        ).put(json=config)

        return r
