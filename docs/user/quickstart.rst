Quickstart
==========

Begin by importing the module. And if you want to silence some warnings go ahead 
and disable them.

::

    >>> import firemon_api as fmapi
    >>> fmapi.disable_warnings()

Create a Firemon object. You will need the name (or IP address) of the FMOS host 
along with a valid username and password.

::

    >>> fm = fmapi.api('saffron', verify=False).auth('firemon', 'firemon')
    >>> fm
    <Firemon(host='saffron', version='9.12.0')>

FireMon has a number of applications such as Security Manager (sm) and Policy Planner (pp)
and each has its own API. Each of these applications, once authed, are available from the
api object as another attribute. Each app also has a simple entry to the api which the user
may use to build requests for calls that may not be covered in other modules or for which
a direct response is more desirable. The following shows examples of making requests that
make use of "building" up of the ``app_url`` or the ``domain_url`` to make building API calls
shorter. The ``/api-doc`` endpoint on your FireMon server should provide documentation for 
queries.

::
    
    >>> fm.sm.app_url
    'https://tuna-9-13-1-aio/securitymanager/api'
    >>> fm.sm.domain_url
    'https://tuna-9-13-1-aio/securitymanager/api/domain/1'

    >>> fm.sm.request(key="collector").get()
    [{'changeThreads': 5, 'commandProcessorMinThreads': 1, 'commandProcessorMaxThreads': 5, 'eventDispatcherThreads': 0, <snip...>]

    >>> fm.sm.request(key="device", use_domain=True).get()
    [{'id': 27, 'domainId': 1, 'name': 'PA-VM 11.0.1', 'managementIp': <snip...>]

    >>> help(fm.sm.request)
    Help on method request in module firemon_api.core.app:

    request(use_domain: Optional[bool] = False, filters: Optional[dict] = None, key: Optional[str] = None, url: Optional[str] = None, headers: Optional[dict] = None, cookies: Optional[dict] = None, trailing_slash: bool = False) -> firemon_api.core.query.Request method of firemon_api.apps.SecurityManager instance

Security Manager
----------------

The ``sm`` Security Manager is the main focus of the module. The general idea is that 
all the main attributes (``endpoints``) should have three main functions to return 
objects of the named type.

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
    |  Parameters:
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
    [<DevicePack(ahnlab_trusguard)>, <DevicePack(aws'>, <DevicePack(aws_vpc)>, <DevicePack(azure)>, <DevicePack(azure_vnet)>, <DevicePack(bluecoat)>, <DevicePack(checkpoint_cma)>,...]

**Device Packs: Filter**

Return a list of all the DevicePack Records based on a filter request.

::

    >>> dp_lst = fm.sm.dp.filter(groupId='com.fm.sm.dp.vmware')
    >>> dp_lst
    [<DevicePack(vmware_distributed_firewall)>, <DevicePack(vmware_edge)>, <DevicePack(vmware_nsx)>]

**Device Packs: Get**

::

    >>> dp = fm.sm.dp.get('juniper_srx')
    >>> dp
    <DevicePack(juniper_srx)>

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

Like Device Packs, Devices contain the same ``all``, ``get``, ``filter`` methods 
along with a number of others. Review the ``help(fm.sm.devices)`` for a full 
listing.

**Devices: All**

Return a list of all the devices currently configured on the SIP instance.

::

    >>> fm.sm.devices.all()
    [<Device(asa-2961.lab.firemon.com)>, <Device(ASA5505-8-3-2)>, <Device(ASA5525_admin)>, <Device(ASA5525_ciscofw2)>, <Device(ASA5525_fm-dev-net-op1-v01i)>, <Device(asav22-67)>,...]


**Devices: Filter**

The filter method uses the APIs specific filter fields. Send a bad filter to get 
the error of required parameters. Most do not require exact information - partial 
is ok.

::

    >>> fm.sm.devices.filter(mgmtip='192.168.200')
    [<Device(asa-2961.lab.firemon.com)>]
    >>> fm.sm.devices.filter(vendors='Cisco')
    [<Device(asa-2961.lab.firemon.com)>, <Device(ASA5505-8-3-2)>, <Device(ASA5525_admin)>, <Device(ASA5525_ciscofw2)>, <Device(ASA5525_fm-dev-net-op1-v01i)>...]


**Devices: Get**

To get a single device the default is to retrieve by the device ID. Retrieval by 
name also works.

::

    >>> dev = fm.sm.devices.get(44)
    >>> dev
    <Device(asa-2961.lab.firemon.com)>
    >>> dev = fm.sm.devices.get('vSRX-3')
    >>> dev
    <Device(vSRX-3)>