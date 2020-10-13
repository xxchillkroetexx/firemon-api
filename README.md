# Firemon-API

This project is for wrapper for the Firemon API.

Learn more on the [Confluence page.](https://confluence.securepassage.com/display/DEVNETSEC/FMAPI%3A+Python+Firemon+API+module)


# Quick Install

Use Lab PyPi. From command line execute `pip`.

```
$ pip install --extra-index-url https://pypi.lab.firemon.com --trusted-host pypi.lab.firemon.com firemon-api
```

Use repo directly. From the command line execute `pip` pointing at the repository.

```
$ pip install git+https://stash.securepassage.com/scm/nsu/firemon-api#egg=firemon-api
```

# Current Design

Everything is basically being coded by hand to attempt to fit a schema that makes sense to me. Endpoints are made and return objects which may have their own functions. For example search and manipulation of devices and their data. This is attempt to make the API a bit more user friendly without requiring more interaction by the user.

I have attempted to create a dynamic interface for all API calls if there is something needed that does not currently fit within the re-imagining of the API schema for user friendliness. Each application should automatically create these. Unfortunately many of the `operationId` for the API are not helpful in what they actually do:

ex: (`get_1`, `get_2`, `get_3`, ...)

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

# Swagger API

I have attempted to dynamically create functions for all the functions referenced in the swagger.json for each application.

To see the swagger.json for each application. Note: It's probably a good idea to enable some logging to see which urls are attempting to be accessed as the swagger operational IDs are not always intuitive. 

```
>>> import firemon_api as fmapi
>>> fmapi.disable_warnings()
>>> fmapi.add_stderr_logger()
>>> fm = fmapi.api('saffron', verify=False).auth('firemon', 'firemon')
>>> fm.sm.get_swagger()
>>> fm.sm.exec.getVersion()
{'fmosVersion': '10.0.0', 'version': '10.0.0-SNAPSHOT', <snip>
>>> fm.gpc.get_swagger()
>>> fm.gpc.exec.getEvents()
[{'id': 30, 'name': 'Access Profile Created', 'gpcEventRelationshipTypes': ['ACCESSPROFILE']}, {'id': 32, 'name': 'Access Profile Deleted', 'gpcEventRelationshipTypes': []}, {'id': 31, 'name': 'Access Profile Updated', 'gpcEventRelationshipTypes': ['ACCESSPROFILE']}, 
{'id': 20, 'name': 'Access Rule Approved',
<snip>
```

# To Do (lots)

Since every call is basically being added by hand there is lots to consider. Mostly finding time to add parts that others might find useful beyond what I have already done for myself.
