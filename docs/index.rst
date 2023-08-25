.. firemon-api documentation master file, created by
   sphinx-quickstart on Sun Apr 16 17:05:23 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

FireMon-API: Python wrapper
===========================

The ``firemon-api`` is an attempt to make a Pythonic wrapper to the FireMon SIP APIs (Security Manager, etc...).

The intent is to hopefully speed up development of projects. There is no intent to do a 1-to-1 reference of all
the potential API calls. If that is desired you may try to use the dynamically built functions created using
the ``get_api()``. There is also no intention to follow any version of the FireMon products and so there may
be instances where a function worked in one version but no longer in another though this generally is not a 
problem.

-------------------

**Quick Example**::

   >>> import firemon_api as fmapi
   >>> fmapi.disable_warnings()
   >>> fm = fmapi.api('saffron', verify=False).auth('firemon', 'firemon')
   >>> fm
   <Firemon(url='https://saffron', version='9.12.0')>
   >>> for dev in fm.sm.devices.all():
   ...   print(dev.name)
   ...
   asa-2961.lab.firemon.com
   ASA5505-8-3-2
   ciscoASA8dot2
   CSM-2
   vSRX-3

   >>> fm.sm.request(key="device", use_domain=True).get()
   [{'id': 27, 'domainId': 1, 'name': 'PA-VM 11.0.1', 'managementIp': <snip...>]

User Guide
----------

.. toctree::
   :maxdepth: 2

   user/install
   user/quickstart
   user/advanced


Security Manager
----------------

.. toctree::
   :maxdepth: 2

   securitymanager/devicepacks
   securitymanager/devices
   securitymanager/users
   securitymanager/siql


Policy Planner
--------------

.. toctree::
   :maxdepth: 2

   policyplanner/workflows
   policyplanner/tickets