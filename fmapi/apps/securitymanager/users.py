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
from urllib.parse import urlencode, quote

# Local packages
from fmapi.errors import AuthenticationError, FiremonError, LicenseError
from fmapi.errors import DeviceError, DevicePackError, VersionError
from fmapi.core.response import Record


class Users(object):
    """ Represents the Users

    Args:
        sm (obj): SecurityManager object
    """

    def __init__(self, sm):
        self.sm = sm
        self.url = sm.domain_url + '/user'  # user URL
        self.session = sm.session

    def all(self):
        """ Get all users

        Return:
            list: List of User(object)

        Raises:
            fmapi.errors.FiremonError: if not status code 200

        Examples:
            >>> users = fm.sm.users.all()
            [..., ..., ..., ..., ]
        """
        url = self.url + '?includeSystem=true&includeDisabled=true&sort=id&pageSize=100'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                return [User(self, user) for user in resp['results']]
            else:
                return None
        else:
            raise FiremonError("ERROR retrieving user! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def get(self, *args, **kwargs):
        """ Get single user

        Args:
            *args (int, optional): User id to retrieve
            **kwargs (str, optional): see filter() for available filters

        Raises:
            fmapi.errors.FiremonError: if not status code 200

        Examples:
            Get by ID
            >>> fm.sm.users.get(2)
            ...
        """
        try:
            id = args[0]
            url = self.url + '/{id}'.format(id=str(id))
            self.session.headers.update({'Content-Type': 'application/json'})
            response = self.session.get(url)
            if response.status_code == 200:
                return User(self, response.json())
            else:
                raise FiremonError("ERROR retrieving user! HTTP code: {}"
                                   " Server response: {}".format(
                                   response.status_code, response.text))
        except IndexError:
            id = None
        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                            "get() returned more than one result. "
                            "Check that the kwarg(s) passed are valid for this "
                            "or use filter() or all() instead."
                        )
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        """ Filter users based on search parameters

        Args:
            **kwargs (str): filter parameters

        Available Filters:
            username, firstName, lastName, email,
            passwordExpired, locked, expired, enabled

        Return:
            list: List of User(objects)
            None: if not found

        Raises:
            fmapi.errors.DeviceError: if not status code 200

        Examples:
            Partial name search return multiple users
            >>> fm.sm.users.filter(username='socra')
            [<User(id='4', username=dc_socrates)>, <User(id='3', username=nd_socrates)>]

            >>> fm.sm.users.filter(enabled=False)
            [<User(id='2', username=workflow)>]

            >>> fm.sm.users.filter(locked=True)
            [<User(id='2', username=workflow)>]
        """
        if not kwargs:
            raise ValueError('filter() must be passed kwargs. ')
        total = 0
        page = 0
        count = 0
        url = self.url + '/filter?page={page}&pageSize=100&filter={filters}'.format(
                            page=page, filters=urlencode(kwargs, quote_via=quote))
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
                    url = self.url + '/filter?page={page}&pageSize=100&filter={filters}'.format(
                                    page=page, filters=urlencode(kwargs, quote_via=quote))
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                return [User(self, user) for user in results]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving users! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    #def create(self, *args, **kwargs):
    #    """ Create a new Collector
    #
    #    Args:
    #        args (dict): a dictionary of all the config settings for a Collector
    #
    #    Return:
    #        int: id for newly created Collector
    #
    #    Examples:
    #
    #    Create by dictionary
    #    >>> fm.sm.c...
    #    """
    #    try:
    #        config = args[0]
    #        config['domainId'] = int(self.domainId)  # API is dumb to auto-fill
    #    except IndexError:
    #        config = None
    #    if not config:
    #        config = kwargs
    #        config['domainId'] = self.domainId # API is dumb to auto-fill
    #    self.session.headers.update({'Content-Type': 'application/json'})
    #    response = self.session.post(self.url, json=config)
    #    if response.status_code == 200:
    #        return json.loads(response.content)['id']
    #    else:
    #        raise FiremonError("ERROR creating collector! HTTP code: {}"
    #                           " Server response: {}".format(
    #                           response.status_code, response.text))

    def __repr__(self):
        return("<Users(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class User(Record):
    """ Represents a User in Firemon

    Args:
        usrs (obj): Users() object
        config (dict): all the things
    """
    def __init__(self, usrs, config):
        super().__init__(usrs, config)

        self.usrs = usrs
        self.url = usrs.sm.domain_url + '/user/{id}'.format(id=str(config['id']))  # User id URL

    def _reload(self):
        """ Todo: Get configuration info upon change """
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(self.url)
        if response.status_code == 200:
            config = response.json()
            self._config = config
            self.__init__(self.api, self._config)
        else:
            raise FiremonError('Error! unable to reload User')

    def enable(self):
        url = self.url + '/enable'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR enableing User! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def disable(self):
        url = self.url + '/disable'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR disabling User! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def unlock(self):
        url = self.url + '/unlock'
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR unlocking User! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def update(self):
        pass

    def __repr__(self):
        return("<User(id='{}', username={})>".format(self.id, self.username))

    def __str__(self):
        return("{}".format(self.username))


class UserGroup(Record):
    """ Represents a UserGroup in Firemon

    Args:
        usrs (obj): Users() object
        config (dict): all the things

    Todo:
        Finish this -
    """
    def __init__(self, usrs, config):
        super().__init__(usrs, config)

        self.usrs = usrs
        self.url = usrs.sm.domain_url + '/user/{id}'.format(id=str(config['id']))  # User id URL
