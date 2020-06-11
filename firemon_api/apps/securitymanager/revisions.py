"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import json
import logging

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request, url_param_builder, RequestError
from firemon_api.core.utils import _build_dict

log = logging.getLogger(__name__)


class Revision(Record):
    """Revision `Record`
    'ndrevisions' and 'normalization'.

    (change configuration &/or normalization state)

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        config (dict): dictionary of things values from json

    Examples:
        >>> rev = fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')[0]
        >>> zip = rev.export()
        >>> with open('export.zip', 'wb') as f:
        ...   f.write(zip)
        ...
        36915
        >>> zip = rev.export(with_meta=False)
        >>> rev.delete()
        True
    """

    ep_name = 'rev'

    def __init__(self, api, app, config):
        super().__init__(api, app, config)
        # app/rev
        #self.url = '{ep}/{id}'.format(ep=self.endpoint.ep_url2, 
        #                                        id=str(config['id']))
        # app/domain-stuff/device-stuff/id
        self.d_url = '{ep}/domain/{did}/device/{devid}/rev/{id}'.format(
                                                ep=self.app_url,
                                                did=str(config['domainId']),
                                                devid=str(config['deviceId']),
                                                id=str(config['id']))

        self.no_no_keys = []

    def save(self):
        raise NotImplementedError(
            "Writes are not supported."
        )

    def update(self):
         raise NotImplementedError(
            "Writes are not supported."
        )

    def changelog(self):
        """ Revision changelog """
        url = '{url}/changelog'.format(url=self.d_url)
        req = Request(
            base=url,
            session=self.session,
        )
        return req.get()

    def export(self, meta: bool=True):
        """Export a zip file contain the config data.
        
        Support files include all NORMALIZED data and other meta data.
        Raw configs include only those files as found by Firemon 
        during a retrieval.

        Kwargs:
            meta (bool): Include metadata and NORMALIZED config files

        Return:
            bytes: zip file
        """
        if meta:
            url = '{url}/export'.format(self.url)
        else:
            url = '{url}/export/config'.format(self.url)
        log.debug('GET {}'.format(self.url))
        response = self.session.get(url)
        if response.status_code == 200:
            return response.content
        else:
            raise RequestError(response)

    def nd_get(self):
        """Get normalized data as a fully parsed object
        
        Retrieve all the revision data in a single payload.
        """
        url = '{url}/nd/all'.format(url=self.url)
        log.debug('GET {}'.format(url))
        response = self.session.get(url)
        if response.status_code == 200:
            return ParsedRevision(self.api, self.app, response.json())
        else:
            raise RequestError(response)

    def nd_problem(self):
        """Get problems with revision"""
        url = '{url}/nd/problem'.format(url=self.d_url)
        req = Request(
            base=url,
            session=self.session,
        )
        return req.get()

    def __repr__(self):
        return("<Revision(id='{}', device='{}')>".format(
                                                    self.id,
                                                    self.deviceId))

    def __str__(self):
        return("{}".format(self.id))


class Revisions(Endpoint):
    """Revisions Endpoint.
    Combining 'ndrevisions' and 'normalization'.
    Filtering is what it is. It is a mixture of revID,
    static domain requirements and device_id, or searching by a subset
    of our internal SIQL (but you cannot search by name or anything in SIQL).

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        device_id (int): Device id

    Examples:
        >>> rev = fm.sm.revisions.get(34)
        >>> rev = fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')[0]
    """

    ep_name = 'rev'

    def __init__(self, api, app,
                record=Revision,
                device_id: int=None):
        super().__init__(api, app, record=Revision)
        self._device_id = device_id

        # Why have one EP when you can have 2+
        # app/rev
        #self.url = "{url}/{ep}".format(url=self.app_url,
        #                                      ep=self.__class__.ep_name)        


    def all(self):
        """Get all `Record`
        """
        if self.device_id:
            all_key = "device/{id}/{ep}".format(id=self.device_id,
                                                     ep=self.__class__.ep_name)
        else:
            all_key = "{ep}".format(ep=self.__class__.ep_name)

        req = Request(
            base=self.domain_url,
            key=all_key,
            session=self.session,
        )

        return [self._response_loader(i) for i in req.get()]

    #def get(self, *args, **kwargs):
    #    """Get single Record
#
    #    Args:
    #        *args (int): (optional) id to retrieve. If this is not type(int)
    #                    dump it into filter and grind it up there.
    #        **kwargs (str): (optional) see filter() for available filters
#
    #    Examples:
    #        Get by ID
    #        >>> fm.sm.revisions.get(1262)
    #        new york
#
    #    """
#
    #    try:
    #        id = int(args[0])
    #        url = '{ep}/{id}'.format(ep=self.url, id=str(id))
    #    except (IndexError, ValueError) as e:
    #        id = None
#
    #    if not id:
    #        if kwargs:
    #            filter_lookup = self.filter(**kwargs)
    #        else:
    #            filter_lookup = self.filter(*args)
    #        if filter_lookup:
    #            if len(filter_lookup) > 1:
    #                raise ValueError(
    #                    "get() returned more than one result. "
    #                    "Check that the kwarg(s) passed are valid for this "
    #                    "endpoint or use filter() or all() instead."
    #                )
    #            else:
    #                return filter_lookup[0]
    #        return None
#
    #    req = Request(
    #        base=url,
    #        session=self.api.session,
    #    )
#
    #    return self._response_loader(req.get())

    def filter(self, *args, **kwargs):
        """ Retrieve a filterd list of Revisions.

        I have no idea how our /filter endpoint works. Some SIQL but
        I cannot find any decent documentation.

        Args:
            **kwargs: key value pairs in a device pack dictionary

        Return:
            list: a list of Revision(object)

        Examples:

        >>> fm.sm.dp.filter(latest=True)
        """

        rev_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [rev for rev in rev_all if kwargs.items() <= dict(rev).items()]

    @property
    def device_id(self):
        return self._device_id


class ParsedRevision(Record):
    """A NORMALIZED Revision. All the things.
    """
    ep_name = 'rev'

    def __init__(self, api, app, config):
        super().__init__(api, app, config)
        self.url = '{ep}/{id}'.format(ep=self.ep_url, 
                                      id=config['revisionId'])

        self.no_no_keys = []

    def save(self):
        """Nothing to save"""
        pass

    def update(self):
        """Nothing to save"""
        pass

    def delete(self):
        """Nothing to delete"""
        pass

    def __repr__(self):
        return("ParsedRevision<(id='{}')>".format(self.revisionId))

    def __str__(self):
        return("{}".format(self.revisionId))
