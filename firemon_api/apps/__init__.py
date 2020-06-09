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
from firemon_api.core.query import Request, url_param_builder

from .globalpolicycontroller import *
from .policyoptimizer import *
from .policyplanner import *
from .securitymanager import *

log = logging.getLogger(__name__)


class App(object):
    """Base class for Firemon Apps

    """

    def __init__(self, api, name):
        self.api = api
        self.session = api.session
        self.name = name
        self.app_url = "{url}/{name}/api".format(url=api.base_url,
                                                name=name)
        self.domain_url = "{url}/domain/{id}".format(url=self.app_url,
                                            id=str(self.api.domain_id))

    def __repr__(self):
        return("<App({})>".format(self.name))

    def __str__(self):
        return('{}'.format(self.name))


class SecurityManager(App):
    """ Represents Security Manager in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * cc: CollectionConfigs()
        * centralsyslogs: CentralSyslogs()
        * collectors: Collectors()
        * collectorgroups: CollectorGroups()
        * devices: Devices()
        * dp: DevicePacks()
        * revisions: Revisions()
        * users: Users()
        * Todo: add more as needed
    """

    def __init__(self, api, name):
        super().__init__(api, name)

        # Endpoints
        self.centralsyslogconfigs = CentralSyslogConfigs(
                                self.api, self, 'centralsyslogconfig')
        self.centralsyslogs = CentralSyslogs(
                                self.api, self, 'central-syslog')
        self.collectionconfigs = CollectionConfigs(
                                self.api, self, 'collectionconfig')
        self.collectors = Collectors(
                                self.api, self, 'collector')
        self.collectorgroups = CollectorGroups(
                                self.api, self, 'collector/group')
        self.devices = Devices(self.api, self, 'device')
        self.dp = DevicePacks(self.api, self, 'plugin')  # Todo: create the other /plugin
        self.revisions = Revisions(self.api, self, 'rev')
        self.users = Users(self.api, self, 'user')

    # Make an es endpoint
    #def es_reindex(self):
    #    """ Mark Elastic Search for reindex """
    #    url = self.sm_url + '/es/reindex'
    #    self.session.headers.update({'Content-Type': 'application/json'})
    #    log.debug('POST {}'.format(self.url))
    #    response = self.session.post(self.url)
    #    if response.status_code == 204:
    #        return True
    #    if response.status_code == 403:
    #        warnings.warn('User is not authorized for request. ',
    #                      AuthenticationWarning)
    #    return False


class GlobalPolicyController(App):
    """ Represents Global Policy Controller in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    def __init__(self, api, name):
        super().__init__(api, name)

        # Endpoints
        #self.xx = EndPoint(self)


class PolicyOptimizer(App):
    """ Represents Policy Optimizer in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    def __init__(self, api, name):
        super().__init__(api, name)

        # Endpoints
        #self.xx = EndPoint(self)


class PolicyPlanner(App):
    """ Represents Policy Planner in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    def __init__(self, api, name):
        super().__init__(api, name)

        # Endpoints
        #self.xx = EndPoint(self)