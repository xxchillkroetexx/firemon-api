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
from typing import Never

# Local packages
from firemon_api.apps import SecurityManager
from firemon_api.core.api import FiremonAPI
from firemon_api.core.response import Record
from firemon_api.core.query import Request, RequestResponse

log = logging.getLogger(__name__)


class SiqlData(Record):
    """A Siql Record."""

    def __init__(self, config, app):
        super().__init__(config, app)

    def save(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported for this Record.")

    def update(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported for this Record.")

    def delete(self, _: Never) -> None:
        raise NotImplementedError("Writes are not supported for this Record.")


class Siql(object):
    """Represent actions on the SIQL endpoint. All functions
    take a `query` which is a string containing the siql.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
    """

    url = None
    ep_name = "siql"
    _is_domain_url = False

    def __init__(self, api: FiremonAPI, app: SecurityManager):
        self.return_obj = SiqlData
        # self.return_obj = JsonField
        self.api = api
        self.session = api.session
        self.app = app
        self.base_url = api.base_url
        self.app_url = app.app_url
        self.domain_url = app.domain_url
        self.url = f"{self.app_url}/{self.__class__.ep_name}"

    def _response_loader(self, values):
        return self.return_obj(values, self.app)

    def _raw(self, query: str, key: str) -> RequestResponse:
        """Raw SIQL query. The incantation used to summon Cthulu.

        Args:
            query (str): SIQL statement
            key (str): endpoint key

            >>> import firemon_api as fmapi
            >>> fm = fmapi.api('carebear-aio', 'firemon', 'firemon')
            >>> s = fm.sm.siql._raw(
                            'device{id=91} | fields(usage(), objUsage())',
                            'secrule/paged-search')
            >>> for rule in s:
            ...   rule, rule.hitCount
            ...   for src in rule.sources:
            ...     src['name'], src['hitcount']
            ...   for dst in rule.destinations:
            ...     dst['name'], dst['hitcount']
            ...   for srv in rule.services:
            ...     srv['name'], srv['hitcount']
            ...
        """
        filters = {"q": query}
        resp = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.api.session,
        ).get()

        return [self._response_loader(i) for i in resp]

    def appobj(self, query):
        return self._raw(query, key="appobj/paged-search")

    def assessment(self, query):
        return self._raw(query, key="assessment/paged-search")

    def asset(self, query):
        return self._raw(query, key="asset/paged-search")

    def control(self, query):
        return self._raw(query, key="control/paged-search")

    def device(self, query):
        return self._raw(query, key="device/paged-search")

    def devicegroup(self, query):
        return self._raw(query, key="devicegroup/paged-search")

    def interface(self, query):
        return self._raw(query, key="interface/paged-search")

    def networkobj(self, query):
        return self._raw(query, key="networkobj/paged-search")

    def natrule(self, query):
        return self._raw(query, key="natrule/paged-search")

    def policy(self, query):
        return self._raw(query, key="policy/paged-search")

    def profileobj(self, query):
        return self._raw(query, key="profileobj/paged-search")

    def scheduleobj(self, query):
        return self._raw(query, key="scheduleobj/paged-search")

    def secrule(self, query):
        return self._raw(query, key="secrule/paged-search")

    def serviceobj(self, query):
        return self._raw(query, key="serviceobj/paged-search")

    def userobj(self, query):
        return self._raw(query, key="userobj/paged-search")

    def urlmatcher(self, query):
        return self._raw(query, key="urlmatcher/paged-search")

    def __repr__(self):
        return f"<Endpoint({self.url})>"

    def __str__(self):
        return f"{self.url}"
