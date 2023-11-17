"""
(c) 2023 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import logging

# Local packages
from firemon_api.core.app import App
from firemon_api.core.response import BaseRecord

log = logging.getLogger(__name__)


class RuleRecommendation(BaseRecord):
    """RuleRecommendation"""

    _ep_name = "rulerec"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def __str__(self):
        return str({self.__class__.__name__})

    def __repr__(self):
        return f"<{self.__class__.__name__}()>"
