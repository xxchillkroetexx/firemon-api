"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Firemon API Error messages

class FiremonError(Exception):
    """Base FiremonError class for all other errors."""


class AuthenticationError(FiremonError):
    """ Raised for authentication failure when connecting to a device. """


class DeviceError(FiremonError):
    """ Raised for problems installing or manipulating devices. """


class DevicePackError(FiremonError):
    """ Raised for errors with manipulating device packs. """


class LicenseError(FiremonError):
    """ Raised for errors pertaining to licensing or license installation. """


class VersionError(FiremonError):
    """ Raised for version overlap when installing device packs. """
