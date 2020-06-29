"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard modules
from urllib.parse import urlencode, quote

# Local packages
from firemon_api.core.query import Request, url_param_builder
from firemon_api.core.response import Record, JsonField


class Endpoint(object):
    """Represent actions available on endpoints
    
    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        record (obj): optional `Record` to use
    """

    url = None
    ep_name = None
    _domain_url = False

    def __init__(self, api, app, record=None):
        if record:
            self.return_obj = record
        else:
            self.return_obj = Record
        self.api = api
        self.session = api.session
        self.app = app
        self.base_url = api.base_url
        self.app_url = app.app_url
        self.domain_url = app.domain_url
        self.url = None
        if self.__class__._domain_url and self.__class__.ep_name:
            self.url = "{url}/{ep}".format(url=self.domain_url,
                                            ep=self.__class__.ep_name)
        elif self.__class__.ep_name:
            self.url = "{url}/{ep}".format(url=self.app_url,
                                            ep=self.__class__.ep_name)

        # These will be used update `key` values for `query.Request`
        # (i.e. they will be appended to 'self.url' to get full path)
        # All child classes can then update to append endpoint actions
        # or add new actions, hopefully for read-ability
        self._ep = {'all': None,
                    'filter': None,
                    'create': None,
                    'count': None,
                   }

    def _response_loader(self, values):
        return self.return_obj(values, self.app)

    def _make_filters(self, values):
        # Our filters do not appear to be standardized across
        # end points. Try and work around them at child classes
        l = []
        for k in values.keys():
            l.append('{}={}'.format(k, values[k]))
        filters = {'filter': l}
        return filters

    def all(self):
        """Get all `Record`
        """
        req = Request(
            base=self.url,
            key=self._ep['all'],
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def get(self, *args, **kwargs):
        """Get single Record

        Args:
            *args (int): (optional) id to retrieve. If this is not type(int)
                        dump it into filter and grind it up there.
            **kwargs (str): (optional) see filter() for available filters

        Examples:
            Get by ID
            >>> fm.sm.centralsyslogs.get(12)
            new york

            Get by partial name. Case insensative.
            >>> fm.sm.centralsyslogs.get(name='detro')
            detroit
        """

        try:
            key = str(args[0])
        except IndexError:
            key = None

        if not key:
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

        req = Request(
            base=self.url,
            key=key,
            session=self.api.session,
        )

        return self._response_loader(req.get())

    def filter(self, *args, **kwargs):
        """Attempt to use the filter options. This is the generic
        Endpoint filter.
        """

        if args:
            # Hopefully this doesn't backfire.
            kwargs.update({"name": args[0]})

        if not kwargs:
            raise ValueError(
                "filter must be passed kwargs. Perhaps use all() instead."
            )

        filters = self._make_filters(kwargs)

        req = Request(
            base=self.url,
            filters=filters,
            key=self._ep['filter'],
            session=self.api.session,
        )

        ret = [self._response_loader(i) for i in req.get()]
        return ret

    def create(self, *args, **kwargs):
        """Creates an object on an endpoint.

        Args:
            args (dict): optional. a dictionary of all the needed options

        Kwargs:
            (str): keywords and args to create a new record

        Return:
            (obj): Record
        """

        req = Request(
            base=self.url,
            key=self._ep['create'],
            session=self.api.session,
        ).post(data=args[0] if args else kwargs)

        if isinstance(req, list):
            return [self._response_loader(i) for i in req]

        return self._response_loader(req)

    def count(self):
        """Returns the count of objects available.
        If there is a 'count' at an endpoint that is used.
        Remember that this is domain dependant and if an Endpoint
        requires a domain we are using that.
        """
        ret = Request(
            base=self.url,
            key=self._ep['count'],
            session=self.api.session,
        )

        return ret.get_count()

    def __repr__(self):
        return("<Endpoint({})>".format(self.url))

    def __str__(self):
        return('{}'.format(self.url))