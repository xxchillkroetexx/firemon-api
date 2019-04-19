"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

def get_return(lookup):
    """Returns simple representations for items passed to lookup. """
    if isinstance(lookup, Record):
        return str(lookup)
    else:
        return lookup


class Record(object):
    """Create python objects for json responses from Firemon

    Example:

    Cast object as a dictionary

    >>> import pprint
    >>> pprint.pprint(dict(x))
    {'all': the.things,
    ...}
    """

    def __init__(self, api, config):
        self._config = config  # keeping a cache just incase bad things
        self._full_cache = []
        self._init_cache = []
        self.api = api
        self.session = api.session
        self.default_ret = Record

        if config:
            self._parse_config(config)

    def _parse_config(self, config):

        def list_parser(list_item):
            if isinstance(list_item, dict):
                return self.default_ret(self.api, list_item)
            return list_item

        for k, v in config.items():
            if isinstance(v, dict):
                lookup = getattr(self.__class__, k, None)
                if lookup:
                    v = lookup(self.api, v)
                else:
                    v = self.default_ret(self.api, v)
                self._add_cache((k, v))
            elif isinstance(v, list):
                v = [list_parser(i) for i in v]
                to_cache = list(v)
                self._add_cache((k, to_cache))
            else:
                self._add_cache((k, v))
            setattr(self, k, v)

    def _add_cache(self, item):
        key, value = item
        self._init_cache.append((key, get_return(value)))

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
        return (getattr(self, "name", None) or getattr(self, "artifactId", None)
                or getattr(self, "id", None) or "")

    def __repr__(self):
        return str(self)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)
