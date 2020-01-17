"""
Firemon API - (firemon-api)

firemon-api is a library to assist in writing Python scripts using Firemon.

    Import the API
    >>> import firemon_api
    >>> fm = firemon_api.api('hobbes', 'firemon', 'firemon')
    >>> fm
    <Firemon(host='hobbes', version='8.25.9')>

    A list of all device packs installed
    >>> fm.sm.dp.all()

    A list of all devices
    >>> fm.sm.devices.all()

    Get a device
    >>> dev = fm.sm.devices.get(name='my-asa')

    Change working domain
    >>> fm.domainId = 2

    Logging for debugging. via urllib3
    >>> import logging
    >>> logging.basicConfig(level=logging.DEBUG)


:copyright: (c) 2019 Firemon

:license: Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Standard Modules
import logging
from logging import NullHandler
import warnings

# Local
from . import errors
from firemon_api.api import FiremonAPI as api

logging.getLogger(__name__).addHandler(NullHandler())

def add_stderr_logger(level=logging.DEBUG):
    """
    Helper for quickly adding a StreamHandler to the logger. Useful for
    debugging.
    Returns the handler after adding it.
    """
    # This method needs to be in this __init__.py to get the __name__ correct
    # even if firemon_api is vendored within another package.
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(
                    logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug("Added a stderr logging handler to logger: %s", __name__)
    return handler

# ... Clean up.
del NullHandler

# All warning filters *must* be appended unless you're really certain that they
# shouldn't be: otherwise, it's very hard for users to use most Python
# mechanisms to silence them.
# AuthenticationWarning's always go off by default.
warnings.simplefilter("always", errors.AuthenticationWarning, append=True)
# Once per host
#warnings.simplefilter("default", errors.SomeWarning, append=True)


def disable_warnings(category=errors.FiremonWarning):
    """
    Helper for quickly disabling all firemon_api warnings.
    """
    warnings.simplefilter("ignore", category)
