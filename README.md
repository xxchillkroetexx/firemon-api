# FireMon-API

This project is for wrapper for the Firemon APIs (Security Manager, etc).

The User Guide available on [Read the Docs](https://firemon-api.readthedocs.io)

# Current Design

Everything is basically being coded by hand to attempt to fit a schema that makes sense to me. Endpoints are made and return objects which may have their own functions. For example search and manipulation of devices and their data. This is attempt to make the API a bit more user friendly without requiring more interaction by the user.

I have attempted to create a dynamic interface for all API calls if there is something needed that does not currently fit within the re-imagining of the API schema for user friendliness. Each application should automatically create these. Unfortunately many of the `operationId` for the API are not helpful in what they actually do:

ex: (`get_1`, `get_2`, `get_3`, ...)

Or use the `/api-doc` from your FireMon server to extrapolate the need keys and methods to make and use the `request()`
function for the specific FireMon application.

```
>>> fm.sm.request(key="device", use_domain=True).get()
[{'id': 27, 'domainId': 1, 'name': 'PA-VM 11.0.1', 'managementIp': <snip...>]
```

# Usage

Import module. Disable unverfied https certificate warnings. Switch https verification off.

```
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
```

Create a new Device. Newer versions of Firemon require we specify which Collector Group and ID to use. Grab the first Collector Group. 

Use all the default information from the device pack for our device.

Add in some required information and other settings to our dictionary.

Create the device.

```
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
```
