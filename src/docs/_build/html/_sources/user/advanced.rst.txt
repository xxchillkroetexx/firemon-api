Advanced Topics
===============

A handful of quick example topics that may be a bit more "advanced"

Requests Sessions
-----------------

Bring your own ``session``. Under-the-hood is `Requests <https://requests.readthedocs.io/en/latest/>` 
and a ``session``. If the one provided is not working as expected just bring your own.

::

    >>> import requests
    >>> import firemon_api as fmapi
    >>> fm = fmapi.api('gizmo').auth('username', 'password')
    >>> s = requests.Session()
    >>> s.auth = ('foo', 'bar')
    >>> s.verify = False
    >>> fm.session = s


Open API
-----------

I have attempted to dynamically create functions for all the functions referenced 
in the ``openapi.json`` for each application. If there is a function not explicitly
made this would be a second way to access every API available.

To see the ``openapi.json`` for each application. 

.. note:: 
    It is probably a good idea to enable the ``std_err_logger`` to view what is being called.
    Dynamically created functions use the supplied ``path``, verb (``get``, ``put``, ``post``, ``delete``)
    and the ``operationId`` to create the function. Unfortunately not always intuitive
    what is being called.

Once the dynamic functions are created they are accessed via the ``exec`` attribute.

::

    >>> import firemon_api as fmapi
    >>> fmapi.disable_warnings()
    >>> fmapi.add_stderr_logger()
    >>> fm = fmapi.api('saffron', verify=False).auth('firemon', 'firemon')
    >>> fm.sm.get_api()
    >>> fm.sm.exec.getVersion()
    {'fmosVersion': '10.0.0', 'version': '10.0.0-SNAPSHOT', <snip>
