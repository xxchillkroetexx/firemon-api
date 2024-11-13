SIQL Queries
============

SIQL queries can be executed in the Python API. Each query fuction has been 
created following the layout of the the ``paged-search`` sections. The SIQL 
query itself is a string of syntax as described in the handbook.


Security Rules
--------------

The follow is a simple query of Security Rules. Be careful to escape '\' 
any quotation marks that will be used in the string if applicable.

::

    import firemon_api as fmapi
    fm = fmapi.api('carebear-aio', verify=False).auth('firemon', 'firemon')
    s = fm.sm.siql.secrule('device{id=91} | fields(usage(), objUsage())')  # string of SIQL for secrule EP
    for rule in s:
    print('Rule: {} : Usage {}'.format(rule, rule.hitCount))
    print('Source Usage')
    for src in rule.sources:
        src['name'], src['hitcount']
    print('Destination Usage')
    for dst in rule.destinations:
        dst['name'], dst['hitcount']
    print('Service Usage')
    for srv in rule.services:
        srv['name'], srv['hitcount']
    Rule: TRUST_access_in_1_1 : Usage 0
    Source Usage
    ('Any', 0)
    Destination Usage
    ('Any', 0)
    Service Usage
    ('Any', 0)