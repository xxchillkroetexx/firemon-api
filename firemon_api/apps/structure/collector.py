from typing import TypedDict


class UsageObjects(TypedDict):
    id: str  # guid
    parentId: str  # guid
    hitCount: int


class RuleUsages(TypedDict, total=False):
    deviceId: int
    ruleId: str  # guid
    sources: list[UsageObjects]
    destinations: list[UsageObjects]
    services: list[UsageObjects]
    apps: list[UsageObjects]
    users: list[UsageObjects]


class Usage(TypedDict):
    endDate: str  # format "YYYY-MM-DDTHH:mm:ss+0000"
    ruleUsages: list[RuleUsages]
    async_aggregation: bool  # ???
