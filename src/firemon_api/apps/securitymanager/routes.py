# Standard packages
import logging
from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.errors import SecurityManagerError
from firemon_api.core.response import BaseRecord
from firemon_api.core.query import Request

log = logging.getLogger(__name__)


class RoutesError(SecurityManagerError):
    pass


class Route(BaseRecord):
    """Device Route Object `Record`.

    Parameters:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "routeobject"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def _url_create(self):
        url = f"{self._ep_url}/{self.deviceid}"
        return url


class Routes(Endpoint):
    """Device Route Object Endpoint.

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
        record (obj): default `Record` object
        device_id (int): Device id
    """

    ep_name = "routeobject/paged-search"
    _is_domain_url = True

    def __init__(
        self,
        api: FiremonAPI,
        app: App,
        record=Route,
        device_id: Optional[int] = None,
    ):
        super().__init__(api, app, record=record)
        self._device_id = device_id

    def all(self) -> list[Route]:
        """Get all `Record`"""
        if self._device_id:
            all_key = f"device/{self._device_id}/{self.__class__.ep_name}"
        else:
            all_key = f"{self.__class__.ep_name}"

        req = Request(
            base=self.domain_url,
            key=all_key,
            session=self.session,
        )

        revs = [self._response_loader(i) for i in req.get()]
        return sorted(revs, key=lambda x: x.deviceid, reverse=True)

    def get(self, *args, **kwargs) -> Route:
        """Query and retrieve individual Routes. Spelling matters.

        Parameters:
            *args: route UUID (matchId)
            **kwargs: key value pairs in a zone dictionary

        Return:
           Route

        Examples:

            >>> fm.sm.routes.get('6014fd68-010d-4437-80cb-8fd4807ba73b')

            >>> fm.sm.routes.get(name='192.168.202.0/23, metric:0')

        """

        route_all = self.all()
        try:
            # Only getting exact matches
            id = args[0]
            route_l = [route for route in route_all if route.matchId == id]
            if len(route_l) > 1:
                raise ValueError(
                    "get() returned more than one result."
                    "Check the kwarg(s) passed are valid or"
                    "use filter() or all() instead."
                )
            elif len(route_l) == 1:
                return route_l[0]
            else:
                raise RoutesError(f"The requested route: {id} could not " "be found")
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

    def filter(self, **kwargs) -> list[Route]:
        """Retrieve a filtered list of Routes

        Parameters:
            **kwargs: key value pairs in a device pack dictionary

        Return:
            list[Route]: a list of Route()

        Examples:

            >>> fm.sm.routes.filter(derived=True)
        """

        route_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [route for route in route_all if kwargs.items() <= dict(route).items()]
