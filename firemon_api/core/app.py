"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
from typing import Callable

from firemon_api.core.api import FiremonAPI
from firemon_api.core.query import Request, RequestResponse

from requests import Session

log = logging.getLogger(__name__)


class DynamicApi(object):
    """Attempt to dynamically create all the APIs

    Warning:
        Most of the names are not intuitive to what they do.
        Good luck and godspeed.
    """

    def __init__(self, dynamic_api: dict, session: Session, app_url: str):
        """
        Args:
            dynamic_api (dict): all the json from `get_api`
        """
        self.session = session
        self.app_url = app_url
        self.url = None
        for path in dynamic_api["paths"].keys():
            for verb in dynamic_api["paths"][path].keys():
                oid = dynamic_api["paths"][path][verb]["operationId"]
                _method = self._make_method(path, verb)
                setattr(self, oid, _method)

    def _make_method(self, path: str, verb: str) -> Callable:
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
        setattr(self, "exec", DynamicApi(_dynamic_api, self.api.session, self.app_url))

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
