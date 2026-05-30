"""
Configuration for entelechy-agentcore.

Supports global configuration (via configure()) and per-adapter overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_ENTELECHY_API_URL = "https://api.mindmods.org"
ENTELECHY_API_URL_ENV = "ENTELECHY_API_URL"
ENTELECHY_API_KEY_ENV = "ENTELECHY_API_KEY"
ENTELECHY_API_TOKEN_ENV = "ENTELECHY_API_TOKEN"


@dataclass
class EntelechyAgentCoreConfig:
    """Global configuration for the AgentCore–Entelechy adapter."""

    entelechy_api_url: str = DEFAULT_ENTELECHY_API_URL
    """Entelechy server URL."""

    api_key: str | None = None
    """API key for Entelechy Cloud. Reads ENTELECHY_API_KEY or ENTELECHY_API_TOKEN if not set."""

    recall_budget: str = "mid"
    """Recall search depth: 'low', 'mid', or 'high'."""

    recall_max_tokens: int = 1500
    """Maximum tokens in the recalled memory block."""

    retain_async: bool = True
    """If True, retain is fire-and-forget (does not block the turn response)."""

    timeout: float = 15.0
    """HTTP timeout in seconds for Entelechy API calls."""

    tags: list[str] = field(default_factory=list)
    """Default tags added to all retained memories."""

    verbose: bool = False
    """Log memory operations."""


_global_config: EntelechyAgentCoreConfig | None = None


def configure(
    entelechy_api_url: str | None = None,
    api_key: str | None = None,
    recall_budget: str = "mid",
    recall_max_tokens: int = 1500,
    retain_async: bool = True,
    timeout: float = 15.0,
    tags: list[str] | None = None,
    verbose: bool = False,
) -> EntelechyAgentCoreConfig:
    """Set the global Entelechy configuration for AgentCore adapters.

    Call once at application startup, before creating any adapters.

    Example:
        from entelechy_agentcore import configure

        configure(
            entelechy_api_url="https://api.mindmods.org",
            api_key=os.environ["ENTELECHY_API_KEY"],
        )
    """
    global _global_config

    resolved_url = entelechy_api_url or os.environ.get(ENTELECHY_API_URL_ENV) or DEFAULT_ENTELECHY_API_URL
    resolved_key = api_key or os.environ.get(ENTELECHY_API_KEY_ENV) or os.environ.get(ENTELECHY_API_TOKEN_ENV)

    _global_config = EntelechyAgentCoreConfig(
        entelechy_api_url=resolved_url,
        api_key=resolved_key,
        recall_budget=recall_budget,
        recall_max_tokens=recall_max_tokens,
        retain_async=retain_async,
        timeout=timeout,
        tags=tags or [],
        verbose=verbose,
    )
    return _global_config


def get_config() -> EntelechyAgentCoreConfig | None:
    """Return the current global config, or None if not yet configured."""
    return _global_config


def reset_config() -> None:
    """Reset the global config to None. Useful in tests."""
    global _global_config
    _global_config = None
