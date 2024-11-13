from typing import Literal
from typing import Optional
from typing import TypedDict


class PolicyPlanRequirementVars(TypedDict, total=False):
    deviceGroupId: int
    expiration: str  # format "YYYY-MM-DDTHH:mm:ss+0000"
    review: str  # format "YYYY-MM-DDTHH:mm:ss+0000"


class PolicyPlanRequirement(TypedDict, total=False):
    requirementType: Literal["RULE", "CLONE"]
    app: Optional[list[str]]
    destinations: list[str]
    services: list[str]
    sources: list[str]
    users: Optional[list[str]]
    childKey: Optional[Literal["add_access"]]
    action: Literal["ACCEPT", "DROP"]
    urlMatchers: Optional[list[str]]
    profiles: Optional[list[str]]
    addressesToClone: Optional[
        list[str]
    ]  # used for "CLONE" type and the list is a single IP
    variables: PolicyPlanRequirementVars
