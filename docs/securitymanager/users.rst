Users
======

Users ``endpoint`` provides access to configured users and returns each user 
as a parsed object.

Endpoint Defaults
-----------------

**All**

Return a list of all the devices currently configured on the SIP instance.

::

    >>> fm.sm.users.all()
    [<User(dc_9-12-0-aio)>, <User(firemon)>, <User(nd_9-12-0-aio)>, <User(workflow)>]


**Filter**

The filter method uses the APIs specific filter fields.

::

    >>> fm.sm.users.filter('aio')
    [<User(dc_9-12-0-aio)>, <User(nd_9-12-0-aio)>]


**Get**

To get a single user.

::

    >>> user = fm.sm.users.get('firemon')
    >>> user
    <User(firemon)>


Standard User Template
----------------------

Retrieve a basic template from which you may create a new user.

::

    >>> config = fm.sm.users.template()
    >>> pprint.pprint(config)
    {'authServerId': None,
    'authType': 'LOCAL',
    'email': None,
    'enabled': True,
    'existingPassword': None,
    'expired': False,
    'firstName': None,
    'lastName': None,
    'locked': False,
    'password': None,
    'passwordExpired': False,
    'username': None}

Create User
-----------

Using the previous examples template we can fill in values to the dictionary and create a user.

::

    >>> config = fm.sm.users.template()
    >>> config['password'] = 'super secret'
    >>> config['username'] = 'frank'
    >>> config['email'] = 'frank@example.com'
    >>> config['firstName'] = 'frank'
    >>> config['lastName'] = 'firemonster'
    >>> fm.sm.users.create(config)
    <User(frank)>

