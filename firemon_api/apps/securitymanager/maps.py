# Standard packages
import logging
from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import BaseEndpoint
from firemon_api.core.response import BaseRecord
from firemon_api.core.query import Request, RequestResponse

log = logging.getLogger(__name__)


class Map(BaseRecord):
    """APA Map Object `BaseRecord`.

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "map"
    _is_domain_url = True

    def __init__(
        self,
        config: dict,
        app: App,
        device_id: Optional[int] = None,
        group_id: int = 1,
    ):
        super().__init__(config, app)
        self._device_id = device_id
        self._group_id = group_id


class Maps(BaseEndpoint):
    """Access Path Maps Object Endpoint.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
        device_id (int): Device id
        group_id (int): Device Group ID
    """

    ep_name = "map"
    _is_domain_url = True

    def __init__(
        self,
        api: FiremonAPI,
        app: App,
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
