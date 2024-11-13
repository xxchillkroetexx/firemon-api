FireMon Applications
====================

FireMon is broken out into a number of applications. Each application gets auto-set to the FireMon API class once a user is authenticated.

::

    >>> import firemon_api as fmapi
    >>> fm = fmapi.auth("goldfin-9-13-0", verify=False).auth('admin', 's3cr3t')
    >>> fm.sm.devices.all()


Each application will have "Endpoints" calls that will return "Records".

Records may have their own methods to act on other data or return other "Records".

If an Endpoint or Record has not been coded up or the user does not feel like dealing with any of the other code that may come with and Endpoint or Record they may make a request against the application directly.

::

    >>> json = fm.sm.request(key="device", use_domain=True).get()

.. toctree::
   :maxdepth: 1

   apps/controlpanel
   apps/orchestration
   apps/policyplanner
   apps/securitymanager
   apps/structures
