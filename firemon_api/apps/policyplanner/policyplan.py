# Standard packages
import logging
from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.errors import PolicyPlannerError
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request

log = logging.getLogger(__name__)


class PolicyPlanError(PolicyPlannerError):
    pass


class Requirement(Record):
    """Represents a Requirement for a policy plan"""

    _ep_name = "requirements"
    _is_domain_url = False

    def __init__(
        self,
        config: dict,
        app: App,
        workflow_id: int,
        ticket_id: int,
        policyplan_url: str,
    ):
        super().__init__(config, app)
        self._workflow_id = workflow_id
        self._ticket_id = ticket_id
        self._policyplan_url = policyplan_url
        self._prechass_url = (
            f"{self._app_url}/prechangeassessments/domain/{self._app._app.api.domain_id}/"
            f"workflow/{self._workflow_id}/packet/{self.workflowPacketId}"
        )

    def set_review_decision(self, decision="APPROVED"):
        """Update workflow requirement approval

        Kwargs:
            decision (str): "APPROVED" | "???"
        """
        key = f"requirement/{self.id}/reviewDecision/{decision}"
        req = Request(
            base=self._prechass_url,
            key=key,
            session=self._session,
        )

        return req.put()


class Requirements(Endpoint):
    """Represents the PolicyPlan Requirements endpoint

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        workflow_id (int): Workflow ID
        ticket_id (int): Packet/Ticket Id

    Kwargs:
        task_id (int): Task ID (this thing... good gravy... it doesn't even matter)
        record (obj): default `Record` object
    """

    ep_name = "requirements"
    _is_domain_url = True

    def __init__(
        self,
        api: FiremonAPI,
        app: App,
        workflow_id: int,
        ticket_id: int,
        task_id: int = 0,
        record=Requirement,
    ):
        self.return_obj = record
        self.api = api
        self.session = api.session
        self.app = app
        self.workflow_id = workflow_id
        self.task_id = task_id  # this is a red herring. the API seems to ignore it
        self.ticket_id = ticket_id
        self.base_url = api.base_url
        self.app_url = app._app_url
        self.domain_url = (
            f"{self.app_url}/policyplan/domain/{self.api.domain_id}/workflow/"
            f"{self.workflow_id}/task/{self.task_id}/packet/{self.ticket_id}"
        )
        self.url = f"{self.domain_url}/{self.__class__.ep_name}"

        self._ep = {
            "all": "",
        }

    def _response_loader(self, values):
        return self.return_obj(
            values, self.app, self.workflow_id, self.ticket_id, self.url
        )

    def all(self) -> list[Requirement]:
        """Get all `Requirement`"""
        req = Request(
            base=self.url,
            key=self._ep["all"],
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def get(self, *args, **kwargs) -> Optional[Requirement]:
        """Query and retrieve individual Requirement.

        Args:
            *args: requirement id

        Return:
            Requirement(object): a Requirement(object)

        Examples:

        >>> pt.requirements.get(9)
        <Requirement(9)>
        """

        requirment_all = self.all()
        try:
            # Only getting exact matches
            id = args[0]
            requirment_l = [
                requirment for requirment in requirment_all if requirment.id == id
            ]
            if len(requirment_l) == 1:
                return requirment_l[0]
            else:
                raise PolicyPlanError(f"The requested Id: {id} could not be found")
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

    def count(self):
        return len(self.all())


class Change(Record):
    """Represents a Change for a policy plan"""

    _ep_name = "changes"
    _is_domain_url = False

    def __init__(
        self,
        config: dict,
        app: App,
        workflow_id: int,
        ticket_id: int,
        policyplan_url: str,
    ):
        super().__init__(config, app)
        self._workflow_id = workflow_id
        self._ticket_id = ticket_id
        self._policyplan_url = policyplan_url
        # self._prechass_url = (
        #    f"{self._app_url}/prechangeassessments/domain/{self._app._app.api.domain_id}/"
        #    f"workflow/{self._workflow_id}/packet/{self.workflowPacketId}"
        # )


class Changes(Endpoint):
    """Represents the PolicyPlan Changes endpoint

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        workflow_id (int): Workflow ID
        ticket_id (int): Packet/Ticket Id

    Kwargs:
        task_id (int): Task ID (this thing... good gravy... it doesn't even matter)
        record (obj): default `Record` object
    """

    ep_name = "changes"
    _is_domain_url = True

    def __init__(
        self,
        api: FiremonAPI,
        app: App,
        workflow_id: int,
        ticket_id: int,
        task_id: int = 0,
        record=Change,
    ):
        self.return_obj = record
        self.api = api
        self.session = api.session
        self.app = app
        self.workflow_id = workflow_id
        self.task_id = task_id  # this is a red herring. the API seems to ignore it
        self.ticket_id = ticket_id
        self.base_url = api.base_url
        self.app_url = app._app_url
        self.domain_url = (
            f"{self.app_url}/policyplan/domain/{self.api.domain_id}/workflow/"
            f"{self.workflow_id}/task/{self.task_id}/packet/{self.ticket_id}"
        )
        self.url = f"{self.domain_url}/{self.__class__.ep_name}"

        self._ep = {
            "all": "",
        }

    def _response_loader(self, values):
        return self.return_obj(
            values, self.app, self.workflow_id, self.ticket_id, self.url
        )

    def all(self) -> list[Change]:
        """Get all `Change`"""
        req = Request(
            base=self.url,
            key=self._ep["all"],
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def get(self, *args, **kwargs) -> Optional[Change]:
        """Query and retrieve individual Change.

        Args:
            *args: change id

        Return:
            Change(object): a Change(object)

        Examples:

        >>> pt.changes.get(9)
        <Change(9)>
        """

        changes_all = self.all()
        try:
            # Only getting exact matches
            id = args[0]
            changes_l = [change for change in changes_all if change.id == id]
            if len(changes_l) == 1:
                return changes_l[0]
            else:
                raise PolicyPlanError(f"The requested Id: {id} could not be found")
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

    def count(self):
        return len(self.all())
