Quickstart
==========

Begin by importing the module. And if you want to silence some warnings go ahead and disable them.

::

    >>> import firemon_api as fmapi
    >>> fmapi.disable_warnings()

Create a Firemon object. You will need the name (or IP address) of the FMOS host along with a valid username and password.

::

    >>> fm = fmapi.api('saffron', verify=False).auth('firemon', 'firemon')
    >>> fm
    <Firemon(host='saffron', version='9.12.0')>


Security Manager
----------------

The ``sm`` Security Manager is the main focus of the module. The general idea is that all the main attributes (``endpoints``) should have three main functions to return objects of the named type.

 * ``all()``: Returns a list of every record
 * ``filter()``: Returns a list filtered down based on the request
 * ``get()``: Gets a single record based on the request

::

    >>> help(fm.sm)
    Help on SecurityManager in module firemon_api.apps object:

    class SecurityManager(App)
    |  SecurityManager(api)
    |
    |  Represents Security Manager in Firemon
    |
    |  Args:
    |      api (obj): FiremonAPI()
    |      name (str): name of the application
    |
    |  Valid attributes are:
    |      * centralsyslogs: CentralSyslogs()
    |      * collectionconfigs: CollectionConfigs()
    |      * collectors: Collectors()
    |      * collectorgroups: CollectorGroups()
    |      * devices: Devices()
    |      * dp: DevicePacks()
    |      * revisions: Revisions()
    |      * users: Users()
    <snip>


Device Packs
------------

**Device Packs: All**

Return a list of all the Device Pack Records

::

    >>> fm.sm.dp.all() 
    [<DevicePack(artifactId='ahnlab_trusguard')>, <DevicePack(artifactId='aws')>, <DevicePack(artifactId='aws_vpc')>, <DevicePack(artifactId='azure')>, <DevicePack(artifactId='azure_vnet')>, <DevicePack(artifactId='bluecoat')>, <DevicePack(artifactId='checkpoint_cma')>,...]

**Device Packs: Filter**

Return a list of all the DevicePack Records based on a filter request.

::

    >>> dp_lst = fm.sm.dp.filter(groupId='com.fm.sm.dp.vmware')
    >>> dp_lst
    [<DevicePack(artifactId='vmware_distributed_firewall')>, <DevicePack(artifactId='vmware_edge')>, <DevicePack(artifactId='vmware_nsx')>]

**Device Packs: Get**

::

    >>> dp = fm.sm.dp.get('juniper_srx')
    >>> dp
    <DevicePack(artifactId='juniper_srx')>

**Device Pack: Attributes**

You can access all the Device Pack Record attributes directly.

::

    >>> dp.artifactId
    'juniper_srx'
    >>> dp.ssh
    True
    >>> dp.id
    85
    >>> dp.deviceType
    'FIREWALL'

Devices
-------

Like Device Packs, Devices contain the same ``all``, ``get``, ``filter`` methods along with a number of others. Review the ``help(fm.sm.devices)`` for a full listing.

**Devices: All**

Return a list of all the devices currently configured on the SIP instance.

::

    >>> fm.sm.devices.all()
    [<Device(id='44', name=asa-2961.lab.firemon.com)>, <Device(id='35', name=ASA5505-8-3-2)>, <Device(id='39', name=ASA5525_admin)>, <Device(id='38', name=ASA5525_ciscofw2)>, <Device(id='36', name=ASA5525_fm-dev-net-op1-v01i)>, <Device(id='40', name=asav22-67)>, <Device(id='42', name=bogus.lab.firemon.com)>, <Device(id='41', name=bogus.lab.securepassage.com)>, <Device(id='43', name=cisco3550sw1)>, <Device(id='45', name=ciscoASA8dot2)>, <Device(id='33', name=CSM-2)>, <Device(id='37', name=fmciscoasa.securepassage.com)>, <Device(id='34', name=fmrouter)>, <Device(id='18', name=vSRX-3)>]


**Devices: Filter**

The filter method uses the APIs specific filter fields. Send a bad filter to get the error of required parameters. Most do not require exact information - partial is ok.

::

    >>> fm.sm.devices.filter(mgmtip='192.168.200')
    [<Device(id='44', name=asa-2961.lab.firemon.com)>]
    >>> fm.sm.devices.filter(vendors='Cisco')
    [<Device(id='44', name=asa-2961.lab.firemon.com)>, <Device(id='35', name=ASA5505-8-3-2)>, <Device(id='39', name=ASA5525_admin)>, <Device(id='38', name=ASA5525_ciscofw2)>, <Device(id='36', name=ASA5525_fm-dev-net-op1-v01i)>, <Device(id='40', name=asav22-67)>, <Device(id='42', name=bogus.lab.firemon.com)>, <Device(id='41', name=bogus.lab.securepassage.com)>, <Device(id='43', name=cisco3550sw1)>, <Device(id='45', name=ciscoASA8dot2)>, <Device(id='33', name=CSM-2)>, <Device(id='37', name=fmciscoasa.securepassage.com)>, <Device(id='34', name=fmrouter)>]


**Devices: Get**

To get a single device the default is to retrieve by the device ID. Retrieval by name also works.

::

    >>> dev = fm.sm.devices.get(44)
    >>> dev
    <Device(id='44', name=asa-2961.lab.firemon.com)>
    >>> dev = fm.sm.devices.get('vSRX-3')
    >>> dev
    <Device(id='18', name=vSRX-3)>