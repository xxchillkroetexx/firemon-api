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
        api (obj): FiremonAPI()
        app (obj): App()
        config (dict): dictionary of things values from json

    Examples:
        Unlock and Enable all users
        >>> for user in fm.sm.users.all():
        ...   user.enabled = True
        ...   user.locked = False
        ...   user.save()
    """

    ep_name = 'user'
    _domain_url = True

    def __init__(self, api, app, config):
        super().__init__(api, app, config)

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
        api (obj): FiremonAPI()
        app (obj): App()
        config (dict): dictionary of things values from json
    """

    ep_name = None

    def __init__(self, api, endpoint, config):
        super().__init__(api, endpoint, config)

