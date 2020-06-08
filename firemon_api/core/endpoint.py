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
from firemon_api.core.response import Record


class Endpoint(object):
    """Represent actions available on endpoints
    
    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint
        record (obj): optional Record() to use
    """

    def __init__(self, api, app, name, record=None):
        if record:
            self.return_obj = record
        else:
            self.return_obj = Record
        self.api = api
        self.session = api.session
        self.app = app
        self.name = name
        self.base_url = api.base_url
        self.app_url = app.app_url
        self.ep_url = "{url}/{ep}".format(url=app.app_url,
                                          ep=name)

    def _response_loader(self, values):
        return self.return_obj(self.api, self, values)

    def all(self):
        """
        """
        req = Request(
            base="{}/".format(self.ep_url),
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def get(self, *args, **kwargs):
        """ Get single Record

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
        url = self.ep_url
        try:
            # Might need to try UUID later?
            id = int(args[0])
            url = '{ep}/{id}'.format(ep=self.ep_url, id=str(id))
        except (IndexError, ValueError) as e:
            id = None

        if not id:
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
            base=url,
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

        # Our filter is the screwiest <sigh>. Seems non-standard
        # revist if our filter style is different at each EP
        filters = ''
        for k in kwargs.keys():
            d = {'filter': '{}={}'.format(k, kwargs[k])}
            filters += '&{}'.format(urlencode(d))

        url = '{ep}/filter?{filters}'.format(ep=self.ep_url, 
                                             filters=filters)

        req = Request(
            base=self.ep_url,
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
            base=self.ep_url,
            session=self.api.session,
        ).post(args[0] if args else kwargs)

        if isinstance(req, list):
            return [self._response_loader(i) for i in req]

        return self._response_loader(req)

    def count(self):
        """Returns the count of objects available.
        If there is a 'count' at an endpoint that is used.
        Remember that this is domain dependant and if an Endpoint
        requires a domain we are using that.
        """
        url = '{ep}/count'.format(ep=self.ep_url)
        ret = Request(
            base=url,
            session=self.api.session,
        )

        return ret.get_count()

    def __repr__(self):
        return("<Endpoint({})>".format(self.name))

    def __str__(self):
        return('{}'.format(self.name))