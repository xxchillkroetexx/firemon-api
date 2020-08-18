# Firemon-API

This project is for wrapper for the Firemon API.

Learn more on the [Confluence page.](https://confluence.securepassage.com/display/DEVNETSEC/FMAPI%3A+Python+Firemon+API+module)


# Quick Install

From the command line execute `pip` pointing at the repository.

```
$ pip install git+https://stash.securepassage.com/scm/nsu/firemon-api#egg=firemon-api
```

# Current Design

Everything is basically being coded by hand to attempt to fit a schema that makes sense to me and usage of objects where calls to endpoints are made and return objects which may have their own functions. For example search and manipulation of devices and their data. This is attempt to make the API a bit more user friendly without requiring more interaction by the user.

I may create a dynamic interface that purely reads the swagger.json from the different APIs and let the user figure it out too.

# Usage

Import module. Disable unverfied https certificate warnings. Switch https verification off.

```
>>> import firemon_api as fmapi
>>> fmapi.disable_warnings()
>>> fm = fmapi.api('saffron', 'firemon', 'firemon', verify=False)
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

# To Do (lots)

Since every call is basically being added by hand there is lots to consider. Mostly finding time to add parts that others might find useful beyond what I have already done for myself.
