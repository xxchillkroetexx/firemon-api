from typing import Literal
from typing import Optional
from typing import TypedDict


class ChangeRequestRequirement(TypedDict):
    action: Literal["ACCEPT", "DROP"]
    apps: Optional[list[str]]
    destinations: list[str]
    profiles: Optional[list[str]]
    services: list[str]  # cisco formatted service. tcp/80, udp/5001-5002/9001
    sources: list[str]
    urlMatchers: Optional[list[str]]
    users: Optional[list[str]]


class ChangeRequestOptions(TypedDict):
    strategy: Literal["NAME_PATTERN", "HITCOUNT", "REFERENCES", "NONE"]
    forceTiebreak: Optional[bool]
    pattern: Optional[str]
    deviceId: Optional[list[int]]
    deviceGroupId: Optional[int]
    addressMatchingStrategy: Literal["INTERSECTS", "SUPERSET_OF"]
    allowAnonymous: bool
    modifyBehavior: Literal["CREATE", "MODIFY", "BOTH"]
    managerRecMethod: Literal["BALANCED", "FEWEST_CHANGES", "LEAST_ACCESS"]


class RuleRecRequirement(TypedDict):
    accept: bool
    applications: Optional[list[str]]
    destinations: list[str]
    profiles: Optional[list[str]]
    services: list[str]  # cisco formatted service. tcp/80, udp/5001-5002/9001
    sources: list[str]
    urlMatchers: Optional[list[str]]
    users: Optional[list[str]]
    sourceMatchingStrategy: Optional[
        Literal["INTERSECTS", "SUPERSET_OF"]
    ]  # Planner defaults to INTERSECTS but RuleRec defaults to SUPERSET_OF
    destinationMatchingStrategy: Optional[
        Literal["INTERSECTS", "SUPERSET_OF"]
    ]  # Planner defaults to INTERSECTS but RuleRec defaults to SUPERSET_OF
