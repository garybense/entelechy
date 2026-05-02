class EntelechyAgentCoreError(Exception):
    """Exception raised when a Entelechy memory operation fails inside AgentCore Runtime."""

    pass


class BankResolutionError(EntelechyAgentCoreError):
    """Raised when bank ID resolution fails — fails closed to prevent memory leakage."""

    pass
