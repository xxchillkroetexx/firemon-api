# Standard packages
import json
import logging
import urllib

# Local packages
from firemon_api.core.endpoint import EndpointCpl
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder, RequestError
from firemon_api.core.utils import _build_dict, _find_dicts_with_key

log = logging.getLogger(__name__)


class Value(Record):
    pass


class Config(EndpointCpl):

    ep_name = "config"

    def __init__(self, api, app):
        """
        Args:
            swagger (dict): all the json from `get_api`
        """
        super().__init__(api, app)
        for cat in self.categories()["categories"]:
            if cat["stub"]:
                continue
            name = cat["label"].lower().replace(" ", "_")
            _method = self._make_cat(cat["path"])
            setattr(self, name, _method)

    def _make_cat(self, path):
        def _method():
            key = urllib.parse.quote(path, safe="")
            req = Request(
                base=self.url,
                key=key,
                session=self.session,
            )
            return req.get()

        return _method

    def categories(self):
        key = "categories"
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()
        return req
