# Standard packages
import logging

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record

log = logging.getLogger(__name__)


class CentralSyslogConfig(Record):
    """Central Syslog Config Record

    Parameters:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "centralsyslogconfig"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)


class CentralSyslogConfigs(Endpoint):
    """Central Syslog Configs Endpoint

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
        record (obj): default `Record` object
    """

    ep_name = "centralsyslogconfig"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=CentralSyslogConfig):
        super().__init__(api, app, record=record)

    def filter(self, *args, **kwargs) -> list[CentralSyslogConfig]:
        """
        Returns:
            list[CentralSyslogConfig]
        """
        csc_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [csc for csc in csc_all if kwargs.items() <= dict(csc).items()]

    def count(self) -> int:
        """
        Returns:
            int
        """
        return len(self.all())
