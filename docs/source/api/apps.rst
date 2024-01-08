FireMon Applications
====================

FireMon is broken out into a number of applications. Each application gets auto-set to the FireMon API class once a user is authenticated.

::

    >>> import firemon_api as fmapi
    >>> fm = fmapi.auth("goldfin-9-13-0", verify=False).auth('admin', 's3cr3t')
    >>> fm.sm.devices.all()

.. toctree::
   :maxdepth: 1

   apps/controlpanel
   apps/orchestration
   apps/policyplanner
   apps/securitymanager
   apps/structures
