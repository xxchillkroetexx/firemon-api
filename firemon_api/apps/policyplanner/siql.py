"""
(c) 2020 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import logging

# Local packages
# from firemon_api.core.endpoint import Endpoint
from firemon_api.apps import PolicyPlanner
from firemon_api.core.api import FiremonAPI
from firemon_api.core.query import Request
from firemon_api.apps.securitymanager.siql import SiqlData

log = logging.getLogger(__name__)


class SiqlPP(object):
    """Represent actions on the SIQL Policy Planner endpoint. All functions
    take a `query` which is a string containing the siql.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
    """

    url = None
    ep_name = "siql"
    _is_domain_url = False

    def __init__(self, api: FiremonAPI, app: PolicyPlanner):
        self._return_obj = SiqlData
        # self.return_obj = JsonField
        self.api = api
        self.session = api.session
        self.app = app
        self.base_url = api.base_url
        self.app_url = app.app_url
        self.domain_url = app.domain_url
        self.url = f"{self.app_url}/{self.__class__.ep_name}"

    def _response_loader(self, values):
        return self._return_obj(values, self.app)
        # return self.return_obj()

    def _raw(self, query: str, key: str) -> SiqlData:
        """Raw SIQL query. The incantation used to summon Cthulu.

        Args:
            query (str): SIQL statement
            key (str): endpoint key
        """
        filters = {"q": query}
        resp = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.api.session,
        ).get()

        return [self._response_loader(i) for i in resp]

    def ticket(self, query: str) -> SiqlData:
        return self._raw(query, key="ticket/paged-search")

    def __repr__(self):
        return f"<Endpoint({self.url})>"

    def __str__(self):
        return f"{self.url}"
