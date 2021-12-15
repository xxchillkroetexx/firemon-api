"""
(c) 2021 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import json
import logging

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder, RequestError
from firemon_api.core.utils import _build_dict

log = logging.getLogger(__name__)


class Route(Record):
    """Device Route Object `Record`.

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:
        >>>
    """

    _ep_name = "routeobject"
    _is_domain_url = True

    def __init__(self, config, app):
        super().__init__(config, app)

    def _url_create(self):
        """ General self._url create. What is normally 'deviceId'. <sigh> """
        url = f"{self._ep_url}/{self.deviceid}"
        return url

    def save(self):
        raise NotImplementedError("Writes are not supported.")

    def update(self):
        raise NotImplementedError("Writes are not supported.")


class Routes(Endpoint):
    """Device Route Object Endpoint.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
        device_id (int): Device id

    Examples:
        >>>
    """

    ep_name = "routeobject/paged-search"
    _is_domain_url = True

    def __init__(self, api, app, record=Route, device_id: int = None):
        super().__init__(api, app, record=Route)
        self._device_id = device_id

    def all(self):
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

    def get(self, *args, **kwargs):
        """Query and retrieve individual Routes. Spelling matters.

        Args:
            *args: route UUID (matchId)
            **kwargs: key value pairs in a zone dictionary

        Return:
            Zone(object): a Zone(object)

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
                raise Exception(f"The requested route: {id} could not " "be found")
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

    def filter(self, **kwargs):
        """Retrieve a filtered list of Routes

        Args:
            **kwargs: key value pairs in a device pack dictionary

        Return:
            list: a list of Route(object)

        Examples:

        >>> fm.sm.routes.filter(derived=True)
        """

        route_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [route for route in route_all if kwargs.items() <= dict(route).items()]
