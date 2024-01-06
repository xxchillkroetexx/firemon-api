"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import logging
from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.errors import SecurityManagerError
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, RequestResponse, RequestError

log = logging.getLogger(__name__)


class SmLoggingError(SecurityManagerError):
    pass


class Logger(Record):
    """Represents a Logger

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "logging"

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def set_level(self, level: str):
        """Sets a logger at the specified level"""
        key = level.upper()
        Request(
            base=self._url,
            key=key,
            session=self._session,
        ).post()

    def reset(self) -> RequestResponse:
        """Reset all logger its default values"""

        Request(
            base=self._url,
            session=self._session,
        ).delete()

    def __str__(self):
        return str((getattr(self, "logger", None)) or "__unknown__")

    def __repr__(self):
        # return str(self)
        return f"<{self.__class__.__name__}({str(self)})>"

    def _parse_config(self, config):
        def list_parser(list_item):
            if isinstance(list_item, dict):
                # Only attempt creating `Logger` if there is a logger attribute.
                if "logger" in list_item.keys():
                    return self._default_ret(list_item, self._app)
            return list_item

        for k, v in config.items():
            if isinstance(v, dict):
                lookup = getattr(self.__class__, k, None)
                if hasattr(lookup, "_json_field"):
                    self._add_cache((k, v.copy()))
                    setattr(self, k, v)
                    continue
                if lookup:
                    v = lookup(v, self._app)
                else:
                    v = self._default_ret(v, self._app)
                self._add_cache((k, v))
            elif isinstance(v, list):
                v = [list_parser(i) for i in v]
                to_cache = list(v)
                self._add_cache((k, to_cache))
            else:
                self._add_cache((k, v))
            setattr(self, k, v)

    def _url_create(self):
        """General self._url create"""
        url = f"{self._ep_url}/{self._config['logger']}"
        return url


class Logging(Endpoint):
    """Represents the Logging

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "logging"

    def __init__(self, api: FiremonAPI, app: App, record=Logger):
        super().__init__(api, app, record=record)

    def all(self) -> list[Logger]:
        """Get all SecMgr loggers

        Examples:

        >>> smloggers = fm.sm.logging.all()
        """

        req = Request(
            base=self.url,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()["loggingLevels"]]

    def filter(self, **kwargs) -> list[Logger]:
        """Retrieve a filtered list of Loggers

        Args:
            **kwargs: `logger`

        Return:
            list: a list of Logger(object)

        Examples:

        >>> fm.sm.logging.filter(logger="com.fm.sm")
        """

        if not kwargs:
            raise ValueError("filter must have kwargs")

        loggers = []
        name = kwargs.get("logger", None)
        for logger in self.all():
            l = dict(logger).copy()
            k = kwargs.copy()
            if name:
                if name in l.get("logger"):
                    del k["logger"]
                    del l["logger"]
                    if k.items() <= l.items():
                        loggers.append(logger)
            else:
                if kwargs.items() <= dict(logger).items():
                    loggers.append(logger)

        return loggers

    def get(self, *args, **kwargs) -> Optional[Logger]:
        """Query and retrieve individual Logger. Spelling matters.

        Args:
            *args: logger name (`logger`)
            **kwargs:

        Return:
            Logger(object): a Logger(object)

        Examples:

        >>> fm.sm.logging.get('com.fm.sm')
        com.fm.sm
        """

        logger_all = self.all()
        try:
            # Only getting exact matches
            id = args[0]
            logger_l = [logger for logger in logger_all if logger.logger == id]
            if len(logger_l) == 1:
                return logger_l[0]
            else:
                raise SmLoggingError(f"The requested logger: {id} could not be found")
        except IndexError:
            id = None

        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result."
                        "Check the kwarg(s) passed are valid or"
                        "use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None

    def reset(self) -> RequestResponse:
        """Reset all loggers to their default values"""

        key = "reset"
        Request(
            base=self.url,
            key=key,
            session=self.api.session,
        ).delete()
