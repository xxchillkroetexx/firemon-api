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
from urllib.parse import urlencode, quote

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request, url_param_builder

log = logging.getLogger(__name__)


class User(Record):
    """ Represents a User in Firemon

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
        
    Examples:
        Unlock and Enable all users
        >>> for user in fm.sm.users.all():
        ...   user.enabled = True
        ...   user.locked = False
        ...   user.save()
    """

    ep_name = 'user'
    _domain_url = True

    def __init__(self, config, app):
        super().__init__(config, app)

    def __repr__(self):
        return("<User(id='{}', username={})>".format(self.id, self.username))

    def __str__(self):
        return("{}".format(self.username))


class Users(Endpoint):
    """ Represents the Users

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = 'user'
    _domain_url = True

    def __init__(self, api, app, record=User):
        super().__init__(api, app, record=User)

    def all(self):
        """Get all `Record`
        """
        filters = {'includeSystem': True, 'includeDisabled': True}

        req = Request(
            base=self.url,
            filters=filters,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def template(self):
        """ Create a template of a simple user

        Return:
            dict: dictionary of data to pass to create
        """
        conf = {}
        conf['username'] = None
        conf['firstName'] = None
        conf['lastName'] = None
        conf['email'] = None
        conf['password'] = None
        conf['existingPassword'] = None
        conf['passwordExpired'] = False
        conf['locked'] = False
        conf['expired'] = False
        conf['enabled'] = True
        conf['authType'] = 'LOCAL'
        conf['authServerId'] = None  # 0
        return conf


class UserGroup(Record):
    """ Represents a UserGroup in Firemon

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
        
    """

    ep_name = 'usergroup'
    _domain_url = True

    def __init__(self, config, app):
        super().__init__(config, app)

    def permission_list(self):
        """ List all available permissions in Firemon. 

        Return:
            list: list of available permissions. 
        """

        key = 'permissiondefinition'
        resp = Request(
            base=self.app.domain_url,
            key=key,
            session=self.session,
            ).get()

        perms = []
        for rg in resp:
            #perms.extend(rg['permissions'])
            for p in rg['permissions']:
                perms.append(Permission(p, self.app))

        return perms

    def permission_show(self):
        key = 'permissions'
        resp = Request(
            base=self.url,
            key=key,
            session=self.session,
            ).get()

        perms = []
        for p in resp:
            perms.append(Permission(p, self.app))

        return perms

    def permission_set(self, id):
        """Set a permision for UserGroup.

        Args:
            id (int): see permission_list() for id values and meaning
        """
        key = 'permission/{}'.format(id)
        resp = Request(
            base=self.url,
            key=key,
            session=self.session,
            ).post()

        return resp

    def permission_unset(self, id):
        """Unset a permision for UserGroup.

        Args:
            id (int): see permission_list() for id values and meaning
        """
        key = 'permission/{}'.format(id)
        resp = Request(
            base=self.url,
            key=key,
            session=self.session,
            ).delete()

        return resp


class UserGroups(Endpoint):
    """Represents the User Groups

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = 'usergroup'
    _domain_url = True

    def __init__(self, api, app, record=UserGroup):
        super().__init__(api, app, record=UserGroup)

    def all(self):
        """Get all `Record`
        """
        filters = {'includeMapping': True}

        req = Request(
            base=self.url,
            filters=filters,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]


class Permission(Record):
    """A Permission.
    """
    ep_name = 'permissions'

    def __init__(self, config, app):
        super().__init__(config, app)

    def save(self):
        raise NotImplementedError(
            "Writes are not supported for this Record."
        )

    def update(self):
        raise NotImplementedError(
            "Writes are not supported for this Record."
        )

    def delete(self):
        raise NotImplementedError(
            "Writes are not supported for this Record."
        )

    def __repr__(self):
        return("Permission<(id='{}')>".format(self.id))

    def __str__(self):
        return("{}".format(self.id))