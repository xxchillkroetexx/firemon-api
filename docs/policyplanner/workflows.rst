Workflows
=========

Workflows ``endpoint`` provides access to configured workflows and returns each workflow 
as a parsed object.

Endpoint Defaults
-----------------

**All**

Return a list of all the workflows currently configured on the SIP instance.

::

    >>> fm.pp.workflows.all()
    [<Workflow(wf__476)>, <Workflow(wf__393)>, <snip...>]

**Get**

Get a single workflow by the workflow ID. You may also get the "default" workflow.

::

    >>> wf = fm.pp.workflows.get(3)
    >>> wf
    <Workflow(wf__913)>

    >>> wf = fm.pp.workflows.default()
    >>> wf
    <Workflow(wf__476)>


Create a Workflow
-----------------

In most cases creating a device requires a few additional bits of information such 
as the management IP of the device, username, password, and a data collector to 
assign the device.

::

    >>> wf = fm.pp.workflows.create(name="Flow_Like_the_Water")
    >>> wf
    <Workflow(Flow_Like_the_Water)>


View and Access Tickets/Packets
-------------------------------

To access and view all the tickets from a workflow.

::

    >>> wf = fm.pp.workflows.default()
    >>> wf.tickets.all()
    [<Packet(1)>]
    >>> ticket = wf.tickets.get(1)
    >>> ticket
    <Packet(1)>