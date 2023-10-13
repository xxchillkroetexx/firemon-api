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
from typing import Literal, Optional, Union

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.query import Request
from firemon_api.core.response import BaseRecord
from firemon_api.apps.structure import RuleRecRequirement, ChangeRequestRequirement

log = logging.getLogger(__name__)


class OrchRuleRecommendation(BaseRecord):
    _ep_name = "rulerec"
    _is_domain_url = True

    def __str__(self):
        return str({self.__class__.__name__})

    def __repr__(self):
        return f"<{self.__class__.__name__}()>"


class ChangeRequest(BaseRecord):
    _ep_name = "change/request"
    _is_domain_url = True


class Changes(Endpoint):
    ep_name = "change/request"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=ChangeRequest):
        super().__init__(api, app, record=record)

    def filter(
        self,
        *args,
        status: Literal["PENDING", "QUEUED", "COMPLETE", "ERROR"] = None,
        **kwargs,
    ) -> list[ChangeRequest]:
        if args:
            _ = args
        if kwargs:
            _ = kwargs

        if not status:
            raise ValueError(
                "filter must be passed `status`. Perhaps use all() instead."
            )

        filters = {"status": status}

        req = Request(
            base=self.url,
            filters=filters,
            key=self._ep["filter"],
            session=self.api.session,
        )

        ret = [self._response_loader(i) for i in req.get()]
        return ret

    def device_rule_rec(
        self,
        device_id: int,
        requirement: RuleRecRequirement,
        license_category: Optional[
            Literal[
                "LOG_SERVERS",
                "ROUTERS",
                "OPERATING_SYSTEMS",
                "FIREWALLS",
                "FIREWALL_MANAGER_MODULES",
                "EDGE_DEVICES",
                "GENERIC_DEVICES",
                "TRAFFIC_MANAGER_MODULES",
                "UNKNOWN",
                "SALES_ONLY_SMLO_HA",
                "SALES_ONLY_SMSO_HA",
                "SALES_ONLY_SMM_HA",
                "POLICY_PLANNER",
                "RISK",
                "POLICY_OPTIMIZER",
                "INSIGHT",
                "GLOBAL_POLICY_CONTROLLER",
                "AUTOMATION",
                "LICENSE_NOT_REQUIRED",
            ]
        ] = None,
        strategy: Literal["NAME_PATTERN", "HITCOUNT", "REFERENCES", "NONE"] = None,
        force_tiebreak: Optional[bool] = None,
        pattern: Optional[str] = None,
        # Leaving these commented out. They seem redundant and don't make sense.
        # device_ids: list[int] = [],
        # device_group_id: int = None,
    ) -> OrchRuleRecommendation:
        key = f"change/device/{device_id}/rulerec"
        filters = {}
        if license_category:
            filters["licenseCategory"] = license_category
        if strategy:
            filters["strategy"] = strategy
        if force_tiebreak:
            filters["forceTiebreak"] = force_tiebreak
        if pattern:
            filters["pattern"] = pattern
        req = Request(
            base=self.domain_url,
            key=key,
            filters=filters,
            session=self.session,
        )
        return OrchRuleRecommendation(req.put(json=requirement), self)

    def rule_rec(
        self,
        requirement: ChangeRequestRequirement,
        license_category: Optional[
            Literal[
                "LOG_SERVERS",
                "ROUTERS",
                "OPERATING_SYSTEMS",
                "FIREWALLS",
                "FIREWALL_MANAGER_MODULES",
                "EDGE_DEVICES",
                "GENERIC_DEVICES",
                "TRAFFIC_MANAGER_MODULES",
                "UNKNOWN",
                "SALES_ONLY_SMLO_HA",
                "SALES_ONLY_SMSO_HA",
                "SALES_ONLY_SMM_HA",
                "POLICY_PLANNER",
                "RISK",
                "POLICY_OPTIMIZER",
                "INSIGHT",
                "GLOBAL_POLICY_CONTROLLER",
                "AUTOMATION",
                "LICENSE_NOT_REQUIRED",
            ]
        ] = None,
        strategy: Literal["NAME_PATTERN", "HITCOUNT", "REFERENCES", "NONE"] = None,
        force_tiebreak: Optional[bool] = None,
        pattern: Optional[str] = None,
        device_ids: Union[int, list[int]] = [],
        device_group_id: int = None,
    ) -> OrchRuleRecommendation:
        key = f"change/rulerec"
        filters = {}
        if license_category:
            filters["licenseCategory"] = license_category
        if strategy:
            filters["strategy"] = strategy
        if force_tiebreak:
            filters["forceTiebreak"] = force_tiebreak
        if pattern:
            filters["pattern"] = pattern
        if device_ids:
            filters["deviceId"] = device_ids
        if device_group_id:
            filters["deviceGroupId"] = device_group_id
        req = Request(
            base=self.domain_url,
            key=key,
            filters=filters,
            session=self.session,
        )
        return OrchRuleRecommendation(req.post(json=requirement), self)
