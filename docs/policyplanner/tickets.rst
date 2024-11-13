Tickets or Packets
==================

Once a user has a workflow object they may access and create tickets/packets.

To access and view all the tickets from a workflow.

::

    >>> wf = fm.pp.workflows.default()
    >>> wf.tickets.all()
    [<Packet(1)>]
    >>> ticket = wf.tickets.get(1)
    >>> ticket
    <Packet(1)>

Automation In Action
--------------------

If a user had their workflow setup to Autodesign their request and their
environment is capable of making correct Rule Recommendations because FireMon
has knowledge of routing then the following example flow will automate changes 
to the users security devices that are licensed for automation.

To create a new ticket the user needs to make a dictionary of values and submit the data.

::

    >>> import datetime
    >>> ticket_defaults = {
    ...     "variables": {
    ...         "requesterName": "Ghost In the Machine",
    ...         "requesterEmail": "example@firemon.com",
    ...         "summary": "auto created ticket",
    ...         "businessNeed": "For Reasons",
    ...         "applicationOwner": "FireMon Tests",
    ...         "applicationName": "Firemon Test App",
    ...         "priority": "LOW",
    ...         "_btnAction": "complete",
    ...     }
    ... }

    >>> now = datetime.datetime.now()
    >>> due = now + datetime.timedelta(days=10)
    >>> ticket_defaults["variables"][
    ...     "dueDate"
    ...    ] = f"{due.strftime('%Y-%m-%d')}T00:00:00.000Z"
    >>> ticket = wf.tickets.create(ticket_defaults)

Every ticket or packet will have a number of "packet tasks". Most often we are concerned
with working on "open" tasks. To know which tasks are listed by the server as "open" we
need to `refresh()` the ticket data and access the open packet task. After acquiring an
open packet task we will want to assign it to ourselves. Since this process of assigning
a task to ourselves occurs frequently it is handy to just make a quick variable to that
data.

::

    >>> user = fm.sm.users.get(fm.username)
    >>> ticket.refresh()
    >>> task = ticket.pt.get_open()
    >>> task.assign(user.id)

Throughout the user will probably want to validate that they are in the proper phase by 
accessing the open packet tasks' workFlowTask information.

::

    >>> task.workflowTask.key
    "_b_reviewTask"

In the "Design" phase the user will want to add requirements. Create requirements as a
dictionary and pass into the packet task. 

::

    >>> requirements = {
    ...     "apps": [],
    ...     "destinations": ["10.3.3.0/27"],
    ...     "services": ["tcp/9050"],
    ...     "sources": ["10.2.2.50"],
    ...     "users": [],
    ...     "requirementType": "RULE",
    ...     "childKey": "add_access",
    ...     "variables": {
    ...         "expiration": None,
    ...         "review": None,
    ...     },
    ...     "action": "ACCEPT",
    ... }
    >>> task.add_requirement(requirements)

In the "Review" stage the user will want to get the open task and approve all changes
and then approve the packet task itself.

::

    >>> ticket.refresh()
    >>> task = ticket.pt.get_open()
    >>> task.assign(user.id)
    >>> for r in task.requirements.all():
    ...     r.set_review_decision()
    >>> task.complete(action="approve")

The user will then want to  execute all the automation requirements. A list of of all 
change id will be made and then executed.

::

    >>> ticket.refresh()
    >>> task = ticket.pt.get_open()
    >>> task.assign(user.id)
    >>> changes = []
    >>> for change in task.changes.all():
    ...     changes.append(change.id)
    >>> task.exec_automation(changes)

The user may also want to check the status of all their automation requests.

::

    >>> ticket.refresh()
    >>> task = ticket.pt.get_open()
    >>> task.assign(user.id)
    >>> if not task:
    ...     print("Automation already completed. Using last task.")
    ...     task = ticket.pt.all()[-1]
    >>> status_in_progress = ("RUNNING", "PENDING", "QUEUED")
    >>> status_failed = ("UNIMPLEMENTED", "FAIL")
    >>> status_passed = ("IMPLEMENTED", "STAGED", "SUCCESS")
    >>> total_in_progress = 0
    >>> total_failed = 0
    >>> total_passed = 0
    >>> for change in task.changes.all():
    ...     if change.implementationStatus in status_in_progress:
    ...         total_in_progress += 1
    ...     elif change.implementationStatus in status_failed:
    ...         total_failed += 1
    ...     elif change.implementationStatus in status_passed:
    ...         total_passed += 1
    >>> print(f"Passed     : {total_passed}")
    >>> print(f"In Progress: {total_in_progress}")
    >>> print(f"Failed     : {total_failed}")