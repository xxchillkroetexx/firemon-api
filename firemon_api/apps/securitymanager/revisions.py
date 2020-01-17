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
from firemon_api.errors import (
    AuthenticationError, FiremonError, LicenseError,
    DeviceError, DevicePackError, VersionError
)
from firemon_api.core.response import Record
from firemon_api.core.utils import _build_dict

log = logging.getLogger(__name__)


class Revisions(object):
    """ Represents the Revisions.
    Filtering is terrible given the API. It is a mixture of revID,
    static domain requirements and deviceID, or searching by a weird subset
    of our internal SIQL (but you cannot search by name or anything in SIQL).
    As a kludge I just ingest all revisions (like the device packs) and create
    get() and filter() functions to parse a dictionary. This may be problematic
    if there are crazy number of revisions but since this is for interal use
    *meh*.

    Args:
        sm (object): SecurityManager()

    Kwargs:
        deviceId (int): Device id

    Examples:
        >>> rev = fm.sm.revisions.get(34)
        >>> rev = fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')[0]
    """
    def __init__(self, sm, deviceId: int=None):
        self.sm = sm
        self.session = sm.session
        self.url = "{sm_url}/rev".format(sm_url=sm.sm_url)
        # Use setter. Intended for use when Revisions is called from Device(objects)
        self._deviceId = deviceId
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
        if self.deviceId:
            url = self.sm.domain_url + ('/device/{deviceId}/rev?sort=id&page'
                                        '={page}&pageSize=100'.format(
                                                        deviceId=self.deviceId,
                                                        page=page))
        else:
            url = self.sm.domain_url + ('/rev?sort=id&page={page}&pageSize'
                                        '=100'.format(page=page))
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
                    if self.deviceId:
                        url = self.sm.domain_url + ('/device/{deviceId}/rev?'
                                'sort=id&page={page}&pageSize=100'.format(
                                            deviceId=self.deviceId,
                                            page=page))
                    else:
                        url = self.sm.domain_url + ('/rev?sort=id&page'
                                    '={page}&pageSize=100'.format(page=page))
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
    def deviceId(self):
        return self._deviceId

    @deviceId.setter
    def deviceId(self, id):
        self._deviceId = id

    def __repr__(self):
        return("<Revisions(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class Revision(Record):
    """ Represents a Revision in Firemon
    The API is painful to use. In some cases the info needed is under
    'ndrevisions' and it other cases it is under 'normalization'. And different
    paths can get the exact same information.

    (change configuration &/or normalization state)

    Args:
        revs: Revisions() object
        config (dict): all the things

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
        self.url2 = revs.sm.domain_url + ('/device/{deviceId}/rev/{revId}'
                                        .format(
                                            deviceId=str(config['deviceId']),
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
            '/device/{deviceId}/rev/{revId}'.format(
                deviceId=str(self.deviceId), revId=str(self.id))
        response = self.session.delete(url)
        if response.status_code == 204:
            return True
        else:
            raise DeviceError("ERROR deleting revision id {}".format(self.id))

    def get_nd(self):
        """Get normalized data as a fully parsed object """
        url = self.url + '/nd/all'
        self.session.headers.update({'Accept': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            return ParsedRevision(self.revs, response.json())
        else:
            raise FiremonError('Error: Unable to retrieve parsed revision')

    def __repr__(self):
        return("<Revision(id='{}', device='{}')>".format(
                                                    self.id,
                                                    self.deviceId))

    def __str__(self):
        return("{}".format(self.id))


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
