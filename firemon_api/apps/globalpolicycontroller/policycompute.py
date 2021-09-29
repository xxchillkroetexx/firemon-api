"""
(c) 2020 Firemon

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
from firemon_api.core.utils import _build_dict
from firemon_api.core.query import Request, url_param_builder

log = logging.getLogger(__name__)


class PolicyCompute(Endpoint):
    """Policy Compute Endpoint

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "policycompute"
    _domain_url = True

    def __init__(self, api, app, record=Record):
        super().__init__(api, app, record=Record)

    def exec(self):
        """Execute a Compute for the domain"""
        key = "computation"

        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.post()

    def all(self):
        raise NotImplementedError("Not supported for this Endpoint.")

    def get(self):
        raise NotImplementedError("Not supported for this Endpoint.")

    def filter(self):
        raise NotImplementedError("Not supported for this Endpoint.")
