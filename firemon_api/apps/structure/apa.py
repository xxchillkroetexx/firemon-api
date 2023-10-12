from typing import TypedDict


class ApaInterface(TypedDict, total=False):
    intfName: str
    virtualRouterId: str  # guid
    routes: bool
    handles: bool
    arps: bool
    gatewayy: bool
