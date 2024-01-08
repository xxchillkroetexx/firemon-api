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
