"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Firemon API Exception messages

class FiremonError(Exception):
    """Base Firemon error used by this module. """
    pass


class AuthenticationError(FiremonError):
    """ Raised for authentication failure when connecting to a device. """
    pass


class DeviceError(FiremonError):
    """ Raised for problems installing or manipulating devices. """
    pass


class DevicePackError(FiremonError):
    """ Raised for errors with manipulating device packs. """
    pass


class LicenseError(FiremonError):
    """ Raised for errors pertaining to licensing or license installation. """
    pass


class VersionError(FiremonError):
    """ Raised for version overlap when installing device packs. """
    pass


# Firemon API Warning messages

class FiremonWarning(Warning):
    """Base Firemon warning used by this module. """
    pass


class AuthenticationWarning(FiremonWarning):
    """ Raised for api calls when user does not have permission """
    pass
