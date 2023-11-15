"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import copy
import logging

from typing import Union, Any

from firemon_api.core.app import App
from firemon_api.core.query import Request
from firemon_api.core.utils import Hashabledict


log = logging.getLogger(__name__)


class JsonField(object):
    """Explicit field type for values that are not to be converted
    to a Record object.

    Basically anything that does not have an `id`
    """

    _json_field = True


class BaseRecord(object):
    """Create python objects for json responses from Firemon

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Example:
        Cast object as a dictionary

        >>> import pprint
        >>> pprint.pprint(dict(x))
        {'all': the.things,
        ...}
    """

    _url = None
    _ep_name = None
    _is_domain_url = False

    def __init__(self, config: dict, app: App):
        self._config = config
        self._init_cache = []
        self._default_ret = Record
        self._app = app
        if getattr(app, "session", None):
            self._session = app.session
            self._base_url = app.base_url
            self._app_url = app.app_url
            self._domain_url = app.domain_url
        else:
            self._session = app._session
            self._base_url = app._base_url
            self._app_url = app._app_url
            self._domain_url = app._domain_url

        self._ep_url = None
        if self.__class__._is_domain_url and self.__class__._ep_name:
            self._ep_url = f"{self._domain_url}/{self.__class__._ep_name}"
        elif self.__class__._ep_name:
            self._ep_url = f"{self._app_url}/{self.__class__._ep_name}"

        if config:
            self._parse_config(config)

        # In almost every case this is the format of the `BaseRecord` url
        # if not, re-work in child class
        if self._ep_url:
            self._url = self._url_create()

    def _url_create(self) -> str:
        """General self._url create"""
        if self._config.get("id", None):
            url = f"{self._ep_url}/{self._config['id']}"
        else:
            url = f"{self._ep_url}"
        return url

    def __iter__(self):
        for i in dict(self._init_cache):
            cur_attr = getattr(self, i)
            if isinstance(cur_attr, Record):
                yield i, dict(cur_attr)
            elif isinstance(cur_attr, list) and all(
                isinstance(i, Record) for i in cur_attr
            ):
                yield i, [dict(x) for x in cur_attr]
            else:
                yield i, cur_attr

    def __getitem__(self, item):
        return item

    def __str__(self):
        return str(
            (getattr(self, "name", None))
            or str(getattr(self, "id", None))
            or "__unknown__"
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}({str(self)})>"

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __key__(self):
        if hasattr(self, "id"):
            return (self.name, self.id)
        else:
            return self.name

    def __hash__(self):
        return hash(self.__key__())

    def __eq__(self, other):
        if isinstance(other, Record):
            return self.__key__() == other.__key__()
        return NotImplemented

    def _add_cache(self, item: tuple[str, Any]) -> None:
        key, value = item
        self._init_cache.append((key, get_return(value)))

    def _parse_config(self, config: Union[list, dict]) -> None:
        def list_parser(list_item):
            if isinstance(list_item, dict):
                # Only attempt creating `Record` if there is an id.
                if "id" in list_item.keys():
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

    def _compare(self) -> bool:
        """Compares current attributes to values at instantiation.
        In order to be idempotent we run this method in `save()`.

        Returns:
            (bool): True indicates current instance has the same
            attributes as the ones passed to `config`.
        """

        if self.serialize(init=True) == self.serialize():
            return True
        return False

    def _diff(self) -> set:
        def fmt_dict(k, v):
            if isinstance(v, dict):
                return k, Hashabledict(v)
            if isinstance(v, list):
                return k, ",".join(map(str, v))
            return k, v

        current = Hashabledict({fmt_dict(k, v) for k, v in self.serialize().items()})
        init = Hashabledict(
            {fmt_dict(k, v) for k, v in self.serialize(init=True).items()}
        )
        return set([i[0] for i in set(current.items()) ^ set(init.items())])

    def serialize(self, nested=False, init=False) -> dict:
        """Serializes an object
        Pulls all the attributes in an object and creates a dict that
        can be turned into the json that Firemon is expecting.
        If an attribute's value is a ``BaseRecord`` type it's replaced with
        the ``id`` field of that object.
        .. note::
            Using this to get a dictionary representation of the record
            is discouraged. It's probably better to cast to dict() or
            dump() instead. See BaseRecord docstring for example. Why? Because
            we are popping out _no_no_keys from the full config in the
            hope that `update()` and `save()` just work

        Return:
            (dict)
        """

        if nested:
            return get_return(self)

        if init:
            init_vals = self._clean_no_no(dict(self._init_cache))

        ret = {}
        for i in self._clean_no_no(dict(self)):
            current_val = getattr(self, i) if not init else init_vals.get(i)

            if isinstance(current_val, BaseRecord):
                current_val = getattr(current_val, "serialize")(nested=True)

            if isinstance(current_val, list):
                current_val = [
                    v.id if isinstance(v, BaseRecord) else v for v in current_val
                ]

            ret[i] = current_val
        return ret

    def dump(self) -> dict:
        """Dump of unparsed config"""
        return copy.deepcopy(self._config)


class Record(BaseRecord):
    """Create python objects for json responses from Firemon

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Example:
        Cast object as a dictionary

        >>> import pprint
        >>> pprint.pprint(dict(x))
        {'all': the.things,
        ...}
    """

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

        self._no_no_keys = []

    def _clean_no_no(self, d: dict) -> dict:
        # remove no_no_keys from a dict. A list of keys for a Record
        # that might break if trying to `save` or `update`
        for k in self._no_no_keys:
            try:
                d.pop(k)
            except KeyError:
                continue
        return d

    def attr_set(self, k: str, v: Union[str, list, dict]) -> None:
        """Set an attribute and add it to the cache
        Firemon will not provide all attributes so you will have
        to just know what you are doing.

        Add a new attribute to `Record`. This is to ensure that
        the `serialize` picks up attribute and `_diff`.

        Args:
            k (str): key/attr
            v (str, list, dict): value
        """
        if isinstance(k, (str)) and isinstance(v, (str, list, dict)):
            if k in dict(self._init_cache).keys():
                setattr(self, k, v)
            else:
                setattr(self, k, v)
                self._add_cache((k, ""))

    def attr_unset(self, k: str) -> None:
        """Unset an attribute and remove from the cache.

        This is to ensure that the `serialize` picks up
        attribute and `_diff`.

        Args:
            k (str): key/attr
        """
        if k in dict(self._init_cache).keys():
            v = dict(self._init_cache)[k]
            self._init_cache.remove((k, v))
            delattr(self, k)

    def save(self) -> bool:
        """Saves changes to an existing object.
        Checks the state of `_diff` and sends the entire
        `serialize` to Request.put(). Note that serialization creates
        a simplified view for all nested objects. These MUST be updated
        at the `Record` level if they go unmodified with `save` being
        overwritten from this simplified version.

        Return:
            (bool): True if PUT request was successful.

        Example:
        >>> dev = fm.sm.devices.get(name='vsrx3')
        >>> dev.name = 'vsrx - updated'
        >>> dev.save()
        True
        >>> dev.description
            ...
        AttributeError: 'Device' object has no attribute 'description'
        >>> dev.add_attr('description', 'new description')
        >>> dev.save()
        True
        >>>
        """
        if self.id:
            diff = self._diff()
            if diff:
                serialized = self.serialize()
                req = Request(
                    base=self._url or self._app.ep_url,
                    key=self.id if not self._url else None,
                    session=self._session,
                )
                req.put(serialized)
                return True

        return False

    def update(self, data: dict) -> bool:
        """Update an object with a dictionary.
        Accepts a dict and uses it to update the record and call save().
        For nested and choice fields you'd pass an int the same as
        if you were modifying the attribute and calling save().

        Args:
            data (dict): Dictionary containing the k/v to update the
            record object with.

        Returns:
            bool: True if PUT request was successful.

        Example:
        >>> dev = fm.sm.devices.get(1)
        >>> dev.update({
        ...   "name": "foo2",
        ...   "description": "barbarbaaaaar",
        ... })
        True
        """

        for k, v in data.items():
            self.attr_set(k, v)
        return self.save()

    def delete(self) -> bool:
        """Deletes an existing object.
        :returns: True if DELETE operation was successful.
        :example:
        >>> dev = fm.sm.devices.get(name='vsrx2')
        >>> dev.delete()
        True
        >>>
        """
        req = Request(
            base=self._url or self._app.ep_url,
            key=self.id if not self._url else None,
            session=self._session,
        )
        return True if req.delete() else False


def get_return(lookup: Any, return_fields=None) -> Any:
    """Returns simple representations for items passed to lookup."""
    for i in return_fields or ["name", "id", "value", "nested_return"]:
        if isinstance(lookup, dict) and lookup.get(i):
            return lookup[i]

    if isinstance(lookup, Record):
        return str(lookup)
    else:
        return lookup
