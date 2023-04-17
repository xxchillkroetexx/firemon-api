Device Packs
============

Device packs are one of a number of plugins. As they are one of the most important 
aspects of the SIP system they get their own ``endpoint`` to access them directly.

Endpoint Defaults
-----------------

**All**

Return a list of all the Device Pack Records currently installed.

::

    >>> fm.sm.dp.all() 
    [<DevicePack(artifactId='ahnlab_trusguard')>, <DevicePack(artifactId='aws')>, <DevicePack(artifactId='aws_vpc')>, <DevicePack(artifactId='azure')>, <DevicePack(artifactId='azure_vnet')>, <DevicePack(artifactId='bluecoat')>, <DevicePack(artifactId='checkpoint_cma')>,...]

**Filter**

Return a list of all the DevicePack Records based on a filter request.

::

    >>> dp_lst = fm.sm.dp.filter(groupId='com.fm.sm.dp.vmware')
    >>> dp_lst
    [<DevicePack(artifactId='vmware_distributed_firewall')>, <DevicePack(artifactId='vmware_edge')>, <DevicePack(artifactId='vmware_nsx')>]

**Get**

::

    >>> dp = fm.sm.dp.get('juniper_srx')
    >>> dp
    <DevicePack(artifactId='juniper_srx')>


Configuration Templates
-----------------------

Device packs may come with a ``layout.json`` file that is used in the user interface to 
provide defaults that will be used to create a device. The ``template()`` function
attempts to provide a similar layout as a Python dictionary.

::

    >>> import pprint
    >>> dp = fm.sm.dp.get('juniper_srx')
    >>> config = dp.template()
    >>> pprint.pprint(config)
    {'description': None,
    'devicePack': {'artifactId': 'juniper_srx',
                    'deviceName': 'SRX',
                    'deviceType': 'FIREWALL',
                    'groupId': 'com.fm.sm.dp.juniper_srx',
                    'id': 61,
                    'type': 'DEVICE_PACK',
                    'version': '9.8.22'},
    'domainId': 1,
    'extendedSettingsJson': {'automationPassword': None,
                            'automationUsername': None,
                            'batchConfigRetrieval': False,
                            'changeMonitoringEnabled': True,
                            'checkForChange': {'intervalInMinutes': 1440},
                            'checkForChangeEnabled': False,
                            'checkForChangeOnChangeDetection': False,
                            'deprecatedCA': False,
                            'encoding': '',
                            'hitCounterRetrievalInterval': 10,
                            'logMonitoringEnabled': True,
                            'logMonitoringMethod': 'Syslog',
                            'logUpdateInterval': 10,
                            'password': '',
                            'port': '22',
                            'resetSSHKeyValue': False,
                            'retrievalCallTimeOut': 120,
                            'retrievalMethod': 'FromDevice',
                            'retrieveSetSyntaxConfig': False,
                            'routesFromConfig': False,
                            'scheduledRetrieval': {'time': None,
                                                    'timeZone': None},
                            'scheduledRetrievalEnabled': False,
                            'serverAliveInterval': 30,
                            'skipRoute': False,
                            'suppressFQDNCapabilities': False,
                            'syslogAlternateIpAddress': None,
                            'useCLICommandGeneration': False,
                            'usePrivateConfig': False,
                            'username': 'admin'},
    'managementIp': None,
    'name': None}

Upload a New Device Pack
------------------------

.. todo::

    To document

