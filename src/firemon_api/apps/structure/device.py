from typing import TypedDict, Literal


class CustomPropertyDefinition(TypedDict, total=False):
    id: int
    name: str
    key: str
    type: Literal["STRING_ARRAY"]
    filterable: bool
    inheritFromMgmtStation: bool


class RuleCustomPropertyDefinition(TypedDict, total=False):
    id: int
    customPropertyDefinition: CustomPropertyDefinition


class RuleDocPoperty(TypedDict, total=False):
    ruleId: str  # guid
    stringarray: list[str]
    ruleCustomPropertyDefinition: RuleCustomPropertyDefinition
    customProperty: CustomPropertyDefinition


class RuleDoc(TypedDict, total=False):
    # If you do not apply an expiration it will be empty even if originally set.
    # Other dates do not appear to be required (may be prefereable to skip)
    ruleId: str  # guid
    deviceId: int
    createDate: str  # format "YYYY-MM-DDTHH:mm:ss+0000"
    lastUpdated: str  # format "YYYY-MM-DDTHH:mm:ss+0000"
    lastRevisionDate: str  # format "YYYY-MM-DDTHH:mm:ss+0000"
    expirationDate: str  # format "YYYY-MM-DDTHH:mm:ss+0000"
