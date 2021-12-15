"""
(c) 2021 Firemon

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
from firemon_api.core.query import Request
from firemon_api.core.utils import _find_dicts_with_key

log = logging.getLogger(__name__)


class Task(Record):

    _ep_name = None
    _is_domain_url = False

    def __init__(self, config, app, name):
        self._name = name
        super().__init__(config, app)

    def save(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def update(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def delete(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def template(self):
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

    def __init__(self, api, app, record=Task):
        super().__init__(api, app, record=Task)

    # Override the default to include "name" for our modified Record
    def _response_loader(self, values, name):
        return self.return_obj(values, self.app, name)

    def all(self):
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

    def get(self, *args, **kwargs):
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

    def filter(self, *args, **kwargs):
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

    def get_services(self, query=None, include_cannot_create=False):
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

    def layout(self, task: str):
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
