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
from typing import Optional, Never

# Local packages
from firemon_api.apps import SecurityManager
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request, RequestResponse

log = logging.getLogger(__name__)


class Map(Record):
    """APA Map Object `Record`.

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:
        >>>
    """

    _ep_name = "map"
    _is_domain_url = True

    def __init__(
        self,
        config: dict,
        app: SecurityManager,
        device_id: Optional[int] = None,
        group_id: int = 1,
    ):
        super().__init__(config, app)
        self._device_id = device_id
        self._group_id = group_id

    def save(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported.")

    def update(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported.")

    def delete(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported.")


class Maps(Endpoint):
    """Access Path Maps Object Endpoint.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
        device_id (int): Device id
        group_id (int): Device Group ID

    Examples:
        >>>
    """

    ep_name = "map"
    _is_domain_url = True

    def __init__(
        self,
        api: FiremonAPI,
        app: SecurityManager,
        record=Map,
        device_id: Optional[int] = None,
        group_id: int = 1,
    ):
        super().__init__(api, app, record=record)
        self._device_id = device_id
        self._group_id = group_id

        if self._device_id:
            self.url = (
                f"{self.domain_url}/device/{self._device_id}/{self.__class__.ep_name}"
            )
        elif self._group_id:
            self.url = f"{self.domain_url}/devicegroup/{self._group_id}/{self.__class__.ep_name}"
        else:
            self.url = f"{self.domain_url}/devicegroup/1/{self.__class__.ep_name}"

    def _response_loader(self, values):
        return self.return_obj(
            values, self.app, device_id=self._device_id, group_id=self._group_id
        )

    def all(self, _: Never) -> None:
        raise NotImplementedError("Unavailable")

    def filter(self, _: Never) -> None:
        raise NotImplementedError("Unavailable")

    def get(self) -> Map:
        """Get `Record`"""

        req = Request(
            base=self.domain_url,
            session=self.session,
        )

        return self._response_loader(req.get())

    def create(self) -> Optional[RequestResponse]:
        """Create/Update `Record`"""
        if self._device_id:
            req = Request(
                base=self.url,
                session=self.session,
            )

            return req.put()
        else:
            raise NotImplemented("unavailable for `devicegroup`")
