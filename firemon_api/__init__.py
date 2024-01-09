"""
Firemon API - (firemon-api)

firemon-api is a library to assist in writing Python scripts using Firemon.

    Import the API

    >>> import firemon_api
    >>> fm = firemon_api.api('hobbes').auth('firemon', 'firemon')
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

    Logging for debugging

    >>> firemon_api.add_stderr_logger()
"""

# Standard Modules
import logging
from logging import NullHandler
from importlib.metadata import version, PackageNotFoundError

# import urllib3

# Local
from firemon_api.core.api import FiremonAPI as api

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    pass


logging.getLogger(__name__).addHandler(NullHandler())


def add_stderr_logger(level=logging.DEBUG):
    """
    Helper for quickly adding a StreamHandler to the logger. Useful for debugging.

    Keyword Arguments:
        level (logging.level)

    Returns:
        handler: the handler after adding it.
    """
    # This method needs to be in this __init__.py to get the __name__ correct
    # even if firemon_api is vendored within another package.
    logger = logging.getLogger(__name__)
    logging.captureWarnings(True)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug("Added a stderr logging handler to logger: %s", __name__)
    return handler


# ... Clean up.
del NullHandler


def disable_warnings():
    """
    Hate warnings? Disable them here.
    """
    # urllib3.disable_warnings()
    import warnings
    from urllib3.exceptions import InsecureRequestWarning

    warnings.filterwarnings("ignore", ".*", UserWarning)
    warnings.filterwarnings("ignore", ".*", InsecureRequestWarning, "urllib3")
