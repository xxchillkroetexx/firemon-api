# Standard packages
import logging
from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import BaseRecord
from firemon_api.core.query import Request, RequestResponse
from firemon_api.core.utils import _find_dicts_with_key

log = logging.getLogger(__name__)


class Task(BaseRecord):
    _ep_name = None
    _is_domain_url = False

    def __init__(self, config: dict, app: App, name: str):
        self._name = name
        super().__init__(config, app)

    def template(self) -> dict:
        """Get default template format for a task.

        Return:
            dict: template information for a task with defaults included
        """
        template = {}

        for response in _find_dicts_with_key("key", self._config):
            # Get rid of headings that are capitalized
            # hopefully all Json name format is followed
            if response["key"][0].isupper():
                continue
            # apparently we are serializing values `key.subkey` "interestingly".
            #   unsure if this is an Angular thing. Told that max of 1 key deep?
            key = None
            sub_key = None
            k_s = response["key"].split(".", maxsplit=1)
            if len(k_s) == 1:
                key = response["key"]
                template.setdefault(key)
            else:
                key = k_s[0]
                sub_key = k_s[1]
                template.setdefault(key, {}).setdefault(sub_key)
            if "defaultValue" in response and not sub_key:
                template[key] = response["defaultValue"]
            elif "defaultValue" in response:
                template[key][sub_key] = response["defaultValue"]

        return template


class Tasks(Endpoint):
    """Represents the Tasks

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "task"
    _is_domain_url = False

    def __init__(self, api: FiremonAPI, app: App, record=Task):
        super().__init__(api, app, record=record)

    # Override the default to include "name" for our modified Record
    def _response_loader(self, values, name):
        return self.return_obj(values, self.app, name)

    def all(self) -> list[Task]:
        tasks = []
        key = "service"
        filters = {"includeCannotCreate": True}

        resp = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        ).get()

        for st in resp:
            layout = self.layout(st["serviceTaskType"])
            tasks.append(self._response_loader(layout, st["serviceTaskType"]))

        return tasks

    def get(self, *args, **kwargs) -> Optional[Task]:
        try:
            name = str(args[0])
        except IndexError:
            name = None

        if not name:
            if kwargs:
                filter_lookup = self.filter(**kwargs)
            else:
                filter_lookup = self.filter(*args)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result. "
                        "Check that the kwarg(s) passed are valid for this "
                        "endpoint or use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None

        key = f"service/form/{name}"

        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )

        return self._response_loader(req.get(), name)

    def filter(self, *args, **kwargs) -> list[Task]:
        """Attempt to use the filter options. Really only a single query

        Kwargs:
            q (str):
        """

        if args:
            kwargs.update({"q": args[0]})

        if not kwargs:
            raise ValueError("filter must be passed kwargs. Perhaps use all() instead.")

        tasks = []
        key = "service"
        filters = {"q": kwargs.get("q", ""), "includeCannotCreate": True}

        resp = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        ).get()

        for st in resp:
            layout = self.layout(st["serviceTaskType"])
            tasks.append(self._response_loader(layout, st["serviceTaskType"]))

        return tasks

    def get_services(self, query: Optional[str] = None, include_cannot_create=False):
        """Retrieve a list of task services

        Kwargs:
            queary (str): if you are inclined to search
            include_cannot_create (bool): default False.
        """

        key = f"service"
        if query:
            filters = {"q": f"{query}", "includeCannotCreate": include_cannot_create}
        else:
            filters = {"includeCannotCreate": include_cannot_create}

        resp = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        ).get()

        return resp

    def layout(self, task: str) -> RequestResponse:
        """Retrieve a task layout.

        Args:
            task (str):
        """

        key = f"service/form/{task}"

        resp = Request(
            base=self.url,
            key=key,
            session=self.session,
        ).get()

        return resp
