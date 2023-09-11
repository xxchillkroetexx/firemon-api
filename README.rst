FireMon-API
===========

This project is for wrapper for the Firemon APIs (Security Manager, etc).

The User Guide available on `Read the Docs <https://firemon-api.readthedocs.io/>` 

Current Philosophy
------------------

The ``firemon-api`` is an attempt to make a Pythonic wrapper to the FireMon SIP APIs (Security Manager, etc...).

The intent is to hopefully speed up development of projects. There is no intent to do a 1-to-1 reference of all
the potential API calls. If that is desired you may try to use the dynamically built functions created using
the ``get_api()``. Or read the ``/api-doc`` of your FireMon product and make use of the ``request()`` function for
the individually created application objects.

**Request Example**::

   >>> fm.sm.request(key="device", use_domain=True).get()
   [{'id': 27, 'domainId': 1, 'name': 'PA-VM 11.0.1', 'managementIp': <snip...>]

There is currently no intention to follow any version of the FireMon products and so there may
be instances where a function worked in one version but no longer in another though this generally is not a 
problem.

Installation of FireMon API
---------------------------

Install ``firemon-api`` into a Python ``venv``.

.. code-block:: console

    ~$ python3 -m venv ~/virtualenvs/fmapi
    ~$ source ~/virtualenvs/fmapi/bin/activate
    (fmapi) ~$ pip install firemon-api
    Collecting firemon-api
    ...


Usage
-----

Import module. Disable unverfied https certificate warnings. Switch https verification off.

::

    >>> import firemon_api as fmapi
    >>> fmapi.disable_warnings()
    >>> fm = fmapi.api('saffron', verify=False).auth('firemon', 'firemon')
    >>> fm
    <Firemon(url='https://saffron', version='10.0.0')>
    >>> for dev in fm.sm.devices.all():
    ...   print(dev.name)
    ...
    asa-2961.lab.firemon.com
    ASA5505-8-3-2
    ciscoASA8dot2
    CSM-2
    vSRX-3


Create a new Device. Newer versions of Firemon require we specify which Collector Group and 
ID to use. Grab the first Collector Group. 

Use all the default information from the device pack for our device.

Add in some required information and other settings to our dictionary.

Create the device.

::

    >>> cg = fm.sm.collectorgroups.all()[0]
    >>> config = fm.sm.dp.get('juniper_srx').template()
    >>> config['name'] = 'Conan'
    >>> config['description'] = 'A test of the API'
    >>> config['managementIp'] = '10.2.2.2'
    >>> config['collectorGroupId'] = cg.id
    >>> config['collectorGroupName'] = cg.name
    >>> config['extendedSettingsJson']['password'] = 'abc12345'
    >>> dev = fm.sm.devices.create(config)
    >>> dev
    <Device(Conan)>

