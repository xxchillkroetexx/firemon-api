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
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder

log = logging.getLogger(__name__)


class License(Endpoint):
    """Represent actions on the License endpoint.
    Most of the other endpoint objects return some `Record`.
    It does not seem to fit here so just a plain `dict` for
    most things is being returned until I figure out better way.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
    """

    url = None
    ep_name = "license"
    _is_domain_url = True

    def __init__(self, api, app):
        super().__init__(api, app)

    def all(self):
        req = Request(
            base=self.url,
            session=self.api.session,
        )

        return req.get()

    def get(self):
        return self.all()

    def filter(self):
        raise NotImplementedError("Filter is not supported for this Endpoint.")

    def count(self):
        raise NotImplementedError("Count is not supported for this Endpoint.")

    def load(self, lic: bytes):
        """Load license file
        Args:
            lic (bytes): bytes that make a license file

        Example:
            >>> fn = '/path/to/file/firemon.lic'
            >>> with open(fn, 'rb') as f:
            >>>     file = f.read()
            >>> fm.sm.license.load(file)
        """
        file = {"file": lic}
        req = Request(
            base=self.url,
            session=self.session,
        )
        return req.post(files=file)
