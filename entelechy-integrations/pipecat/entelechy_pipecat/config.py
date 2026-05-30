"""Global configuration for Entelechy-Pipecat integration."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_ENTELECHY_API_URL = "https://api.mindmods.org"
ENTELECHY_API_KEY_ENV = "ENTELECHY_API_KEY"


@dataclass
class EntelechyPipecatConfig:
    """Connection and default settings for the Pipecat integration.

    Attributes:
        entelechy_api_url: URL of the Entelechy API server.
        api_key: API key for Entelechy authentication.
        recall_budget: Default recall budget level (low/mid/high).
        recall_max_tokens: Default maximum tokens for recall results.
    """

    entelechy_api_url: str = DEFAULT_ENTELECHY_API_URL
    api_key: str | None = None
    recall_budget: str = "mid"
    recall_max_tokens: int = 4096


_global_config: EntelechyPipecatConfig | None = None


def configure(
    entelechy_api_url: str | None = None,
    api_key: str | None = None,
    recall_budget: str = "mid",
    recall_max_tokens: int = 4096,
) -> EntelechyPipecatConfig:
    """Configure Entelechy connection and default settings.

    Args:
        entelechy_api_url: Entelechy API URL (default: production).
        api_key: API key. Falls back to ENTELECHY_API_KEY env var.
        recall_budget: Default recall budget (low/mid/high).
        recall_max_tokens: Default max tokens for recall.

    Returns:
        The configured EntelechyPipecatConfig.
    """
    global _global_config

    resolved_url = entelechy_api_url or DEFAULT_ENTELECHY_API_URL
    resolved_key = api_key or os.environ.get(ENTELECHY_API_KEY_ENV)

    _global_config = EntelechyPipecatConfig(
        entelechy_api_url=resolved_url,
        api_key=resolved_key,
        recall_budget=recall_budget,
        recall_max_tokens=recall_max_tokens,
    )

    return _global_config


def get_config() -> EntelechyPipecatConfig | None:
    """Get the current global configuration."""
    return _global_config


def reset_config() -> None:
    """Reset global configuration to None."""
    global _global_config
    _global_config = None
