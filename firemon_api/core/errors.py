class FiremonApiError(Exception):
    """Generic Firemon API Exception"""


class ControlPanelError(FiremonApiError):
    """Generic CPL Exception"""


class OrchestrationError(FiremonApiError):
    """Generic Orchestration Exception"""


class PolicyOptimizerError(FiremonApiError):
    """Generic Policy Optimizer Exception"""


class PolicyPlannerError(FiremonApiError):
    """Generic Policy Planner Exception"""


class SecurityManagerError(FiremonApiError):
    """Generic Orchestration Exception"""
