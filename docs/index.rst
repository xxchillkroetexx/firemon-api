.. firemon-api documentation master file, created by
   sphinx-quickstart on Sun Apr 16 17:05:23 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

FireMon-API: Python wrapper
===========================

The ``firemon-api`` is an attempt to make a Pythonic wrapper to the FireMon SIP APIs (Security Manager, etc...).

The intent is to hopefully speed up development of projects.

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


User Guide
----------

.. toctree::
   :maxdepth: 2

   user/quickstart


Security Manager
----------------

.. toctree::
   :maxdepth: 2

   securitymanager/devices

