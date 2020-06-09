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
from firemon_api.core.query import Request, url_param_builder
from firemon_api.core.utils import _build_dict

log = logging.getLogger(__name__)


class Revision(Record):
    """ Represents a Revision in Firemon
    The API is painful to use. In some cases the info needed is under
    'ndrevisions' and it other cases it is under 'normalization'. And different
    paths can get the exact same information.

    (change configuration &/or normalization state)

    Args:
        api (obj): FiremonAPI()
        endpoint (obj): Endpoint()
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
    def __init__(self, revs, config):
        super().__init__(revs, config)
        self.revs = revs
        self.url = revs.sm.sm_url + '/rev/{revId}'.format(
                                                        revId=str(config['id']))
        # Because instead of just operating on the revision they needed another
        # path <sigh>
        self.url2 = revs.sm.domain_url + ('/device/{device_id}/rev/{revId}'
                                        .format(
                                            device_id=str(config['device_id']),
                                            revId=str(config['id'])))

    def summary(self):
        return self._config.copy()

    def changelog(self):
        """ Revision changelog """
        total = 0
        page = 0
        count = 0
        url = self.url2 + '/changelog?page={page}&pageSize=100'.format(
                                                                    page=page)
        self.session.headers.update({'Content-Type': 'application/json'})
        log.debug('GET {}'.format(self.url))
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                results = resp['results']
                total = resp['total']
                count = resp['count']
                while total > count:
                    page += 1
                    url = self.url2 + ('/changelog?page={page}&pageSize=100'
                                        .format(page=page))
                    log.debug('GET {}'.format(self.url))
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                return(results)
            else:
                return([])
        else:
            raise FiremonError("ERROR retrieving revisions! HTTP code: {} "
                              "Server response: {}".format(
                                                        response.status_code,
                                                        response.text))

    def export(self, with_meta: bool=True):
        """ Export a zip file contain the config data for the device and,
        optionally, other meta data and NORMALIZED data. Support files in gui.

        Kwargs:
            with_meta (bool): Include metadata and NORMALIZED config files

        Return:
            bytes: zip file
        """
        self.session.headers.pop('Content-type', None)  # If "content-type" exists get rid.
        if with_meta:
            url = self.url + '/export'
        else:
            url = self.url + '/export/config'
        log.debug('GET {}'.format(self.url))
        response = self.session.get(url)
        if response.status_code == 200:
            return response.content
        else:
            raise FiremonError("ERROR retrieving revisions! HTTP code: {}  "
                              "Server response: {}".format(
                                                    response.status_code,
                                                    response.text))

    def delete(self):
        """ Delete the revision

        Return:
            bool: True if deleted
        """
        url = self.revs.sm.domain_url + \
            '/device/{device_id}/rev/{revId}'.format(
                device_id=str(self.device_id), revId=str(self.id))
        log.debug('DELETE {}'.format(self.url))
        response = self.session.delete(url)
        if response.status_code == 204:
            return True
        else:
            raise DeviceError("ERROR deleting revision id {}".format(self.id))

    def get_nd(self):
        """Get normalized data as a fully parsed object """
        url = self.url + '/nd/all'
        self.session.headers.update({'Accept': 'application/json'})
        log.debug('GET {}'.format(self.url))
        response = self.session.get(url)
        if response.status_code == 200:
            return ParsedRevision(self.revs, response.json())
        else:
            raise FiremonError('Error: Unable to retrieve parsed revision')

    def __repr__(self):
        return("<Revision(id='{}', device='{}')>".format(
                                                    self.id,
                                                    self.device_id))

    def __str__(self):
        return("{}".format(self.id))


class Revisions(Endpoint):
    """ Represents the Revisions.
    Filtering is terrible given the API. It is a mixture of revID,
    static domain requirements and device_id, or searching by a weird subset
    of our internal SIQL (but you cannot search by name or anything in SIQL).
    As a kludge I just ingest all revisions (like the device packs) and create
    get() and filter() functions to parse a dictionary. This may be problematic
    if there are crazy number of revisions but since this is for interal use
    *meh*.

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
    def __init__(self, api, app, name, device_id: int=None):
        super().__init__(api, app, name)
        self._device_id = device_id
        if self.device_id:
            self.ep_url = "{url}/device/{id}/{ep}".format(
                                                    url=app.domain_url,
                                                    id=device_id,
                                                    ep=name)
        else:
            self.ep_url = "{url}/{ep}".format(url=app.domain_url,
                                              ep=name)
        self._revisions = {}

    def _get_all(self):
        """ Retrieve a dictionary of revisions. This is effectively a kludge
        since we do not have direct access to /rev endpoint so we will injest
        all then parse locally.

        Returns:
            dict: a dictionary that contains revision info
        """
        total = 0
        page = 0
        count = 0
        if self.device_id:
            url = self.sm.domain_url + ('/device/{device_id}/rev?sort=id&page'
                                        '={page}&pageSize=100'.format(
                                                        device_id=self.device_id,
                                                        page=page))
        else:
            url = self.sm.domain_url + ('/rev?sort=id&page={page}&pageSize'
                                        '=100'.format(page=page))
        log.debug('GET {}'.format(self.url))
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                results = resp['results']
                total = resp['total']
                count = resp['count']
                while total > count:
                    page += 1
                    if self.device_id:
                        url = self.sm.domain_url + ('/device/{device_id}/rev?'
                                'sort=id&page={page}&pageSize=100'.format(
                                            device_id=self.device_id,
                                            page=page))
                    else:
                        url = self.sm.domain_url + ('/rev?sort=id&page'
                                    '={page}&pageSize=100'.format(page=page))
                    log.debug('GET {}'.format(self.url))
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                self._revisions = _build_dict(results, 'id')
            else:
                self._revisions = {}
        else:
            raise FiremonError("ERROR retrieving revisions! HTTP code: {} "
                              "Server response: {}".format(
                                                response.status_code,
                                                response.text))

    def all(self):
        """ Get all revisions

        Return:
            list: a list of Revision(object)

        Examples:

            >>> revs = fm.sm.revisions.all()
        """
        #if not self._revisions:
        #    self._get_all()
        self._get_all()
        return [Revision(self, self._revisions[id]) for id in self._revisions]

    def get(self, *args, **kwargs):
        """ Query and retrieve individual Revision

        Args:
            *args (int): The revision ID
            **kwargs: key value pairs in a revision dictionary

        Return:
            Revision(object): a single Revision(object)

        Examples:

            >>> fm.sm.revisions.get(3)
            3
            >>> rev = fm.sm.revisions.get(3)
            >>> type(rev)
            <class 'firemon_api.apps.securitymanager.Revision'>
            >>> rev = fm.sm.revisions.get(correlationId='7a5406e4-93de-44af-8ed1-0e4135458324')
            >>> rev
            11
        """
        #if not self._revisions:
        #    self._get_all()
        self._get_all()
        try:
            id = args[0]
            rev = self._revisions[id]
            if rev:
                return Revision(self, rev)
            else:
                raise FiremonError("ERROR retrieving revison")
        except (KeyError, IndexError):
            id = None

        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError("get() returned more than one result."
                                    "Check the kwarg(s) passed are valid or"
                                    "use filter() or all() instead.")
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        """ Retrieve a filterd list of Revisions

        Args:
            **kwargs: key value pairs in a revision dictionary

        Return:
            list: a list of Revision(object)

        Examples:

            >>> fm.sm.revisions.filter(deviceName='vSRX-2')
            [76, 77, 108, 177, 178]

            >>> fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')
            [178]

            >>> fm.sm.revisions.filter(deviceType='FIREWALL')
            [3, 4, 5, 6, 7, 8, 9,

            >>> fm.sm.revisions.filter(latest=True)
            [1, 2, 3, 6, 8, 9, 10, 13, 14, 75, 122, 153, 171, 174, 178, 189]
        """
        #if not self._revisions:
        #    self._get_all()
        self._get_all()

        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [Revision(self, self._revisions[id]) for id in
                self._revisions if kwargs.items()
                <= self._revisions[id].items()]

    @property
    def device_id(self):
        return self._device_id

    @device_id.setter
    def device_id(self, id):
        self._device_id = id


class ParsedRevision(Record):
    """A dynamic representation of all the NORMALIZED things

    Todo:
        Document the JSON/Record information and key values purpose
            or at least some of the major ones
    """
    def __repr__(self):
        return("ParsedRevision<(id='{}')>".format(self.revisionId))

    def __str__(self):
        return("{}".format(self.revisionId))
