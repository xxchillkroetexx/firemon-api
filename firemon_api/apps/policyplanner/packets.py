"""
(c) 2021 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Standard packages
import datetime
import logging
from typing import Optional, TypedDict

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import BaseRecord, Record
from firemon_api.core.query import Request, RequestResponse
from firemon_api.apps.structure import PolicyPlanRequirement
from .siql import SiqlPP
from .policyplan import Changes, Requirements

log = logging.getLogger(__name__)


class PacketTaskError(Exception):
    pass


class PacketTask(Record):
    """Represents the Packet Task for the Packet/Ticket record"""

    _ep_name = "packet-task"
    _is_domain_url = True

    def __init__(self, config: dict, app: App, packet_id: int):
        super().__init__(config, app)
        self._packet_id = packet_id
        self._wf_id = self._config["workflowTask"]["workflowVersion"]["id"]
        self._task_id = self._config["workflowTask"]["id"]

        self._ep_url = (
            f"{self._domain_url}/workflow/{self._wf_id}/"
            f"task/{self._task_id}/packet/{self._packet_id}/{self.__class__._ep_name}"
        )

        self._policyplan_url = (
            f"{self._app_url}/policyplan/domain/{self._app._app.api.domain_id}/"
            f"workflow/{self._config['workflowTask']['workflowVersion']['id']}/"
            f"task/{self._task_id}/packet/{self._packet_id}"
        )
        self._url = self._url_create()

        self.changes = Changes(
            self._app._app.api,
            self._app,
            self._wf_id,
            self._packet_id,
            task_id=self._task_id,  # red herring - anything works
        )

        self.requirements = Requirements(
            self._app._app.api,
            self._app,
            self._wf_id,
            self._packet_id,
            task_id=self._task_id,  # red herring - anything works
        )

    def add_requirement(self, config: PolicyPlanRequirement) -> RequestResponse:
        """Add a requirement

        Args:
            config (PolicyPlanRequirement): dict of requirements
        """

        key = f"requirement"
        req = Request(
            base=self._policyplan_url,
            key=key,
            session=self._session,
        )
        return req.post(json=config)

    def assign(self, id: str) -> RequestResponse:
        """Assign a packet task"""
        key = "assign"
        headers = self._session.headers
        headers.update({"Content-Type": "text/plain"})
        req = Request(
            base=self._url,
            key=key,
            headers=headers,
            session=self._session,
        )
        return req.put(data=str(id))

    def unassign(self) -> RequestResponse:
        """Unassign a packet task"""
        key = "unassign"
        headers = self._session.headers
        headers.update({"Content-Type": "text/plain"})
        req = Request(
            base=self._url,
            key=key,
            headers=headers,
            session=self._session,
        )
        return req.put()

    def complete(self, action: str = "submit") -> RequestResponse:
        """Complete a packet task

        Kwargs:
            button (str): "submit" | "approve"
        """
        key = "complete"
        filters = {"button": f"{action}"}
        req = Request(
            base=self._url,
            key=key,
            filters=filters,
            session=self._session,
        )
        return req.put()

    def exec_automation(self, changes: list[int]) -> RequestResponse:
        """Execute automation for all changes

        Args:
            changes (list): a list of change id
        """
        if not changes:
            raise PacketTaskError("Unable to automate. No changes provided")
        key = "changes/automate"
        filters = {"changeId": changes}
        req = Request(
            base=self._url,
            key=key,
            filters=filters,
            session=self._session,
        )
        return req.post()


class PacketTasks(Endpoint):
    """Represents the Packet Task for the Packets/Tickets endpoint

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        packet_id (int): Packet Id

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "packet-tasks"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, packet_id: int, record=PacketTask):
        self.return_obj = record
        self.api = api
        self.session = api.session
        self.app = app
        self.base_url = api.base_url
        self.app_url = app._app_url
        self.domain_url = app._domain_url
        self.url = None
        if self.__class__._is_domain_url and self.__class__.ep_name:
            self.url = f"{self.domain_url}/{self.__class__.ep_name}"
        elif self.__class__.ep_name:
            self.url = f"{self.app_url}/{self.__class__.ep_name}"

        # These will be used update `key` values for `query.Request`
        # (i.e. they will be appended to 'self.url' to get full path)
        # All child classes can then update to append endpoint actions
        # or add new actions, hopefully for read-ability
        self._ep = {
            "all": None,
            "filter": None,
            "create": None,
            "count": None,
        }
        self._packet_id = packet_id

    def _response_loader(self, values, packet_id):
        return self.return_obj(values, self.app, packet_id)

    def all(self) -> list[PacketTask]:
        p_tasks = []
        for wfpt in sorted(
            self.app._config["workflowPacketTasks"], key=lambda p: p["id"]
        ):
            p_tasks.append(self._response_loader(wfpt, self._packet_id))
        return p_tasks

    def get(self, *args, **kwargs) -> Optional[PacketTask]:
        """Query and retrieve individual PacketTask

        Args:
            *args: packet task id
            **kwargs: key value pairs in a device pack dictionary

        Return:
            PacketTask(object): a PacketTask(object)

        Examples:

        >>>
        """

        pt_all = self.all()
        try:
            # Only getting exact matches
            id = args[0]
            pt_l = [pt for pt in pt_all if pt.id == id]
            if len(pt_l) == 1:
                return pt_l[0]
            else:
                raise Exception(f"The requested Packet Task: {id} could not be found")
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

    def filter(self, **kwargs) -> list[PacketTask]:
        """Retrieve a filterd list of PacketTasks

        Args:
            **kwargs: key value pairs in a device pack dictionary

        Return:
            list: a list of PacketTask(object)

        Examples:

        >>>
        """

        pt_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [pt for pt in pt_all if kwargs.items() <= dict(pt).items()]

    def last_modified(self) -> PacketTask:
        """Get task by last modified date"""
        return sorted(
            self.all(),
            key=lambda p: datetime.datetime.fromisoformat(
                p.lastModifiedDate.rstrip("Z")
            ),
        )[0]

    def get_open(self) -> Optional[PacketTask]:
        """Get the task that is not completed"""
        packet_task = None
        for pt in reversed(self.all()):
            if not pt.dump().get("completed", ""):
                return pt
        return packet_task


class Packet(BaseRecord):
    """Represents the Packet/Ticket record"""

    _ep_name = "packet"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)
        self._wf_id = self._config["workflowVersion"]["id"]

        if self.__class__._is_domain_url and self.__class__._ep_name:
            self._ep_url = (
                f"{self._domain_url}/workflow/{self._wf_id}/{self.__class__._ep_name}"
            )
        self._url = self._url_create()

        self.pt = PacketTasks(self._app.api, self, self.id)

    def refresh(self):
        key = f"{self.id}"
        req = Request(
            base=self._ep_url,
            key=key,
            session=self._session,
        )
        self.__init__(req.get(), self._app)


class Packets(Endpoint):
    """Represents the Packets/Tickets endpoint

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "packet"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, wf_id: int, record=Packet):
        super().__init__(api, app, record=record)
        self._wf_id = wf_id

        if self.__class__._is_domain_url and self.__class__.ep_name:
            self.url = (
                f"{self.domain_url}/workflow/{self._wf_id}/{self.__class__.ep_name}"
            )

    def all(self) -> list[Packet]:
        siql_ep = SiqlPP(self.api, self.app)
        siql = f"ticket{{workflow={self._wf_id}}}"
        tickets = siql_ep.ticket(siql)
        return [self.get(ticket.id) for ticket in tickets]

    def get(self, *args, **kwargs) -> Optional[Packet]:
        try:
            id = str(args[0])
        except IndexError:
            id = None

        if not id:
            if kwargs:
                filter_lookup = self.filter(**kwargs)
            else:
                filter_lookup = self.filter(*args)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result. "
                        "Check that the kwarg(s) passed are valid for this "
                        "endpoint or use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None

        key = f"{id}"

        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )

        return self._response_loader(req.get())

    def filter(self, *args, **kwargs) -> list[Packet]:
        """Attempt to use the filter options. Really only a single query

        Kwargs:
            siql (str): whatever siql query for tickets is available
        """

        if args:
            kwargs.update({"siql": args[0]})

        if not kwargs:
            raise ValueError("filter must be passed kwargs. Perhaps use all() instead.")

        siql_ep = SiqlPP(self.api, self.app)
        siql = f"ticket{{{kwargs['siql']}}}"
        tickets = siql_ep.ticket(siql)
        return [self.get(ticket.id) for ticket in tickets]

    def create(self, config: dict = None) -> Packet:
        """Create a workflow packet/ticket instance

        Kwargs:
            config (dict):
        """

        if not config:
            config = {}

        resp = Request(
            base=self.url,
            session=self.session,
        ).post(json=config)

        return self._response_loader(resp)
