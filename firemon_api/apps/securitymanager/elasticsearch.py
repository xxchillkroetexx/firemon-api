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
# from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder

log = logging.getLogger(__name__)


class ElasticSearch(object):
    """Represent actions on the Elastic Search endpoint.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
    """

    url = None
    ep_name = "es"
    _is_domain_url = False

    def __init__(self, api, app):
        # self.return_obj = Record
        # self.return_obj = JsonField
        self.api = api
        self.session = api.session
        self.app = app
        self.base_url = api.base_url
        self.app_url = app.app_url
        # self.domain_url = app.domain_url
        self.url = f"{self.app_url}/{self.__class__.ep_name}"

    def reindex(self):
        """Mark Elastic Search for reindex"""
        key = "reindex"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.post()
