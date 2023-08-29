"""
(c) 2021 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Standard packages
import logging

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request, RequestResponse, RequestError
from .packets import Packets, Packet

log = logging.getLogger(__name__)


class Workflow(Record):
    """Workflow Record"""

    _ep_name = "workflow"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

        self.tickets = Packets(self._app.api, self._app, config["id"])

        self._no_no_keys = [
            "createdBy",
            "createdDate",
            "lastModifiedBy",
            "lastModifiedDate",
        ]

    def save(self) -> RequestResponse:
        if self.id:
            diff = self._diff()
            if diff:
                serialized = self.serialize()
                # Make sure this is set appropriately. Cannot change.
                serialized["id"] = self._config["id"]
                log.debug(serialized)
                req = Request(
                    base=self._url,
                    key="config",
                    session=self._session,
                )
                req.put(serialized)
                return True

        return False

    def update(self, data: dict) -> RequestResponse:
        for k, v in data.items():
            self.attr_set(k, v)

        return self.save()

    def delete(self) -> None:
        raise NotImplementedError("Writes are not supported for this Record.")

    def disable(self) -> RequestResponse:
        Request(
            base=self._url,
            key="disable",
            session=self._session,
        ).put()
        return True

    def enable(self) -> RequestResponse:
        Request(
            base=self._url,
            key="enable",
            session=self._session,
        ).put()
        return True

    def start_properties(self) -> RequestResponse:
        resp = Request(
            base=self._url,
            key="start-properties",
            session=self._session,
        ).get()
        return resp

    def tasks(self) -> RequestResponse:
        resp = Request(
            base=self._url,
            key="tasks",
            session=self._session,
        ).get()
        return resp


class Workflows(Endpoint):
    """Represents the Workflows

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "workflow"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=Workflow):
        super().__init__(api, app, record=record)

    def create(self, name: str, config: dict = None) -> Workflow:
        """Create a new Workflow

        Args:
            name (str): Name of the new workflow

        Kwargs:
            config (dict): dictionary of configuration data.

        Return:
            Workflow (obj): a Workflow() of the newly created workflow

        Examples:

        """
        key = f"plugin/com.fm.wf.pp/access-request"
        filters = {"name": name}

        if not config:
            config = {}
            config["name"] = name
            config["createDateSortDir"] = False

        resp = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        ).post(json=config)

        return self.get(resp["id"])

    def default(self) -> Workflow:
        """Get default workflow"""

        req = Request(
            base=self.url,
            key="default",
            session=self.session,
        )

        try:
            return self._response_loader(req.get())
        except RequestError:
            log.debug(f"No default workflow")
            return None
