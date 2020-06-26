"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging

from firemon_api.core.query import Request
from firemon_api.core.utils import Hashabledict

log = logging.getLogger(__name__)

def get_return(lookup, return_fields=None):
    """Returns simple representations for items passed to lookup. """
    for i in return_fields or ["id", "value", "nested_return"]:
        if isinstance(lookup, dict) and lookup.get(i):
            return lookup[i]

    if isinstance(lookup, Record):
        return str(lookup)
    else:
        return lookup


class JsonField(object):
    """Explicit field type for values that are not to be converted
    to a JsonRecord object. 
    
    Basically anything that does not have an `id`
    """
    _json_field = True


class Record(object):
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

    url = None
    ep_name = None
    _domain_url = False

    def __init__(self, config, app):
        self._config = config
        self._init_cache = []   
        self.default_ret = Record
        self.app = app
        self.session = app.session
        self.base_url = app.base_url
        self.app_url = app.app_url
        self.domain_url = app.domain_url
        self.ep_url = None
        if self.__class__._domain_url and self.__class__.ep_name:
            self.ep_url = "{url}/{ep}".format(url=self.domain_url,
                                            ep=self.__class__.ep_name)
        elif self.__class__.ep_name:
            self.ep_url = "{url}/{ep}".format(url=self.app_url,
                                            ep=self.__class__.ep_name)

        if config:
            self._parse_config(config)

        # In almost every case this is the format of the `Record` url
        # if not, re-work in child class
        if self.ep_url:
            self.url = self._url_create()

        self._no_no_keys = []

    def _url_create(self):
        """ General self.url create """
        url = '{ep}/{id}'.format(ep=self.ep_url, 
                                        id=self._config['id'])
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
        return (getattr(self, "name", None) or 
                getattr(self, "id", None) or "__unknown__")

    def __repr__(self):
        #return("Record<({})>".format(str(self)))
        return str(self)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __key__(self):
        if hasattr(self, "id"):
            return (self.name, self.id)
        else:
            return (self.name)

    def __hash__(self):
        return hash(self.__key__())

    def __eq__(self, other):
        if isinstance(other, Record):
            return self.__key__() == other.__key__()
        return NotImplemented

    def _add_cache(self, item):
        key, value = item
        self._init_cache.append((key, get_return(value)))

    def _parse_config(self, config):

        def list_parser(list_item):
            if isinstance(list_item, dict):
                # Only attempt creating `Record` if there is an id.
                if 'id' in list_item.keys():
                     return self.default_ret(list_item, self.app)
            return list_item

        for k, v in config.items():
            if isinstance(v, dict):
                lookup = getattr(self.__class__, k, None)
                if hasattr(lookup, "_json_field"):
                    self._add_cache((k, v.copy()))
                    setattr(self, k, v)
                    continue
                if lookup:
                    v = lookup(v, self.app)
                else:
                    v = self.default_ret(v, self.app)
                self._add_cache((k, v))
            elif isinstance(v, list):
                v = [list_parser(i) for i in v]
                to_cache = list(v)
                self._add_cache((k, to_cache))
            else:
                self._add_cache((k, v))
            setattr(self, k, v)

    def _compare(self):
        """Compares current attributes to values at instantiation.
        In order to be idempotent we run this method in `save()`.

        Returns:
            (bool): True indicates current instance has the same
            attributes as the ones passed to `config`.
        """

        if self.serialize(init=True) == self.serialize():
            return True
        return False

    def _clean_no_no(self, d):
        # remove no_no_keys from a dict. A list of keys for a Record
        # that might break if trying to `save` or `update`
        for k in self._no_no_keys:
            try:
                d.pop(k)
            except KeyError:
                continue
        return(d)

    def serialize(self, nested=False, init=False):
        """Serializes an object
        Pulls all the attributes in an object and creates a dict that
        can be turned into the json that Firemon is expecting.
        If an attribute's value is a ``Record`` type it's replaced with
        the ``id`` field of that object.
        .. note::
            Using this to get a dictionary representation of the record
            is discouraged. It's probably better to cast to dict() or
            dump() instead. See Record docstring for example. Why? Because
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
            log.debug(current_val)

            if isinstance(current_val, Record):
                current_val = getattr(current_val, "serialize")(
                    nested=True
                )

            if isinstance(current_val, list):
                current_val = [
                    v.id if isinstance(v, Record) else v
                    for v in current_val
                ]

            ret[i] = current_val
        return ret

    def _diff(self):
        def fmt_dict(k, v):
            if isinstance(v, dict):
                return k, Hashabledict(v)
            if isinstance(v, list):
                return k, ",".join(map(str, v))
            return k, v

        current = Hashabledict(
            {fmt_dict(k, v) for k, v in self.serialize().items()}
        )
        init = Hashabledict(
            {fmt_dict(k, v) for k, v in self.serialize(init=True).items()}
        )
        return set([i[0] for i in set(current.items()) ^ set(init.items())])

    def dump(self):
        """Dump of unparsed config"""
        return self._config.copy()

    def attr_set(self, k, v):
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
                self._add_cache((k, ''))

    def attr_unset(self, k):
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

    def save(self):
        """Saves changes to an existing object.
        Checks the state of `_diff` and sends the entire
        `serialize` to Request.put().

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
                    base=self.url or self.endpoint.ep_url,
                    key=self.id if not self.url else None,
                    session=self.api.session,
                )
                return req.put(serialized)

        return False

    def update(self, data):
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

    def delete(self):
        """Deletes an existing object.
        :returns: True if DELETE operation was successful.
        :example:
        >>> dev = fm.sm.devices.get(name='vsrx2')
        >>> dev.delete()
        True
        >>>
        """
        req = Request(
            base=self.url or self.endpoint.ep_url,
            key=self.id if not self.url else None,
            session=self.api.session,
        )
        return True if req.delete() else False