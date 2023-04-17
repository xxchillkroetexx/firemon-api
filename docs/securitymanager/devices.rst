Devices
=======

Devices ``endpoint`` provides access to configured devices and returns each device 
as a parsed object.

Endpoint Defaults
-----------------

**All**

Return a list of all the devices currently configured on the SIP instance.

::

    >>> fm.sm.devices.all()
    [<Device(asa-2961.lab.firemon.com)>, <Device(ASA5505-8-3-2)>, <Device(ASA5525_admin)>, <Device(ASA5525_ciscofw2)>, <Device(ASA5525_fm-dev-net-op1-v01i)>, <Device(asav22-67)>,...]


**Filter**

The filter method uses the APIs specific filter fields. Send a bad filter to get the 
error of required parameters. Most do not require exact information - partial is ok.

::

    >>> fm.sm.devices.filter(mgmtip='192.168.200')
    [<Device(asa-2961.lab.firemon.com)>]
    >>> fm.sm.devices.filter(vendors='Cisco')
    [<Device(asa-2961.lab.firemon.com)>, <Device(ASA5505-8-3-2)>, <Device(ASA5525_admin)>, <Device(ASA5525_ciscofw2)>, <Device(ASA5525_fm-dev-net-op1-v01i)>...]


**Get**

To get a single device the default is to retrieve by the device ID. Retrieval by 
name also works.

::

    >>> dev = fm.sm.devices.get(44)
    >>> dev
    <Device(asa-2961.lab.firemon.com)>
    >>> dev = fm.sm.devices.get('vSRX-3')
    >>> dev
    <Device(vSRX-3)>


Create a Device
---------------

In most cases creating a device requires a few additional bits of information such 
as the management IP of the device, username, password, and a data collector to 
assign the device.

::

    >>> import random
    >>> config = fm.sm.dp.get('cisco_pix_asa_fwsm').template()
    >>> cg = random.choice(fm.sm.collectorgroups.all())
    >>> config["collectorGroupId"] = cg.id
    >>> config['name'] = "ASA-device"
    >>> config['extendedSettingsJson']['username'] = 'asauser'
    >>> config['extendedSettingsJson']['password'] = 'secretpassword'
    >>> config['extendedSettingsJson']['enablePassword'] = 'secretenable'
    >>> config['managementIp'] = '10.2.2.2'
    >>> dev = fm.sm.devices.create(config, retrieve=True)
    >>> dev.revisions.all()
    [<Revision(23)>]


Modify a Device
---------------

A full devices config may be seen by running the ``dump()`` function for a device. But 
when it comes to modifying a device's configuration much of that information may cause 
API errors so to get around that many ``Records`` will have a ``serialize()`` method 
to assist in getting on the needed data which can be modified and reloaded.

.. note::
    Normal users will not have access to sensitive data such as passwords. The user
    will want to make sure any such masked fields are updated to reflect their
    configuration.

::

    >>> dev = fm.sm.devices.get("ASA-device")
    >>> config = dev.serialize()
    >>> config['extendedSettingsJson']['enablePassword'] = 'enablepwupdate'
    >>> config['extendedSettingsJson']['password'] = 'secretupdate'
    >>> config['description'] = "Packet denier"
    >>> dev.update(config, retrieve=False)
    True
    >>> dev = fm.sm.devices.get("ASA-device")
    >>> pprint.pprint(dev.dump())
    {'children': [],
    'collectorGroupId': 'c2882aff-2bf3-4f21-b40c-07581d8e021c',
    'collectorGroupName': 'goldfin-9-8-4-aio.lab.firemon.com-Group',
    'description': 'Packet denier',
    <snip>...

Delete Device and Child Devices
-------------------------------

You may normally just run ``delete()`` function to delete a device. If the 
device in question has children you need to delete each child in turn or 
specify the ``deleteChildren`` argument. The following example would delete 
every device on the system.

::

    >>> for dev in fm.sm.devices.all():
    ...    if dev.devicePack.deviceType in ("APPLICATION_LIBRARY"):
    ...        print(
    ...            "[!] Skipping because this is a device that isn't a device."
    ...        )
    ...        continue
    ...    if dev.parents:
    ...        continue  # delete the parent instead
    ...    try:
    ...        dev.delete(deleteChildren=True)
    ...        print(f"[+] Deleted {dev.name}")
    ...    except:
    ...        print(f"[-] Failed to delete {dev.name}")
    ...        pass

Device Rule Usage
-----------------

You may access rule usage in a number of ways. Directly from the device for 
a total usage. Or using a SIQL query and adding up individual rules usage.

::

    >>> dev.rule_usage()
    {'totalHits': 392}

    >>> siql = f"device{{id={dev.id}}} | fields(usage(), objUsage())"
    >>> secrules = fm.sm.siql.secrule(siql)
    >>> siql_count = 0
    >>> for rule in secrules:
    ...    siql_count += rule.hitCount
    >>> siql_count
    392

Perform a Retrieval
-------------------

Kick off a manual retrieval for a device.

::

    >>> dev.retrieval_exec()
    True

Get Device Revisions
--------------------

You may access revisions filtered by device. This will show all revisions 
regardless of the status.

::

    >>> dev.revisions.all()
    [<Revision(24)>, <Revision(23)>]

Get Device Latest Successful Revision and Normalized Data
---------------------------------------------------------

You may access the latest successful revision. Once you have a revision 
you may access details about the revision and also retrieve the revisions 
normalized data.

::

    >>> rev = dev.rev_latest_get()
    >>> rev.id, rev.status
    (20, 'NORMALIZED')
    >>> nd = rev.nd_get()
    >>> nd.interfaces
    [<Record(GigabitEthernet0/0)>, <Record(SecDMZ)>, <Record(GigabitEthernet0/2)>, <Record(GigabitEthernet0/3)>, <Record(GigabitEthernet0/4)>, <Record(GigabitEthernet0/5)>, <Record(GigabitEthernet0/6)>, <Record(GigabitEthernet0/7)>, <Record(GigabitEthernet0/8)>, <Record(Trust)>, <Record(identity)>]

Create Support Export with Normalized Data
------------------------------------------

Once you have a revision you may make a support file that includes the 
raw file data and all normalized data.

::

    >>> rev = dev.rev_latest_get()
    >>> fn = f"/var/tmp/{rev.deviceName.replace(' ', '_').replace('/', '_')}_rev-{rev.id}.zip"
    >>> fn
    '/var/tmp/ASAv-9_rev-20.zip'
    >>> f_zip = rev.export(meta=True)
    >>> with open(fn, "wb") as f:
    ...     f.write(f_zip)
    ...
    41033
