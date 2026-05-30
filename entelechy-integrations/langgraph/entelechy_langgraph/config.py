"""Global configuration for Entelechy-LangGraph integration."""

import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_ENTELECHY_API_URL = "https://api.mindmods.org"
ENTELECHY_API_KEY_ENV = "ENTELECHY_API_KEY"


@dataclass
class EntelechyLangGraphConfig:
    """Connection and default settings for the LangGraph integration.

    Attributes:
        entelechy_api_url: URL of the Entelechy API server.
        api_key: API key for Entelechy authentication.
        budget: Default recall budget level (low/mid/high).
        max_tokens: Default maximum tokens for recall results.
        tags: Default tags applied when storing memories.
        recall_tags: Default tags to filter when searching memories.
        recall_tags_match: Tag matching mode (any/all/any_strict/all_strict).
        verbose: Enable verbose logging.
    """

    entelechy_api_url: str = DEFAULT_ENTELECHY_API_URL
    api_key: Optional[str] = None
    budget: str = "mid"
    max_tokens: int = 4096
    tags: Optional[list[str]] = None
    recall_tags: Optional[list[str]] = None
    recall_tags_match: str = "any"
    verbose: bool = False


_global_config: Optional[EntelechyLangGraphConfig] = None


def configure(
    entelechy_api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    budget: str = "mid",
    max_tokens: int = 4096,
    tags: Optional[list[str]] = None,
    recall_tags: Optional[list[str]] = None,
    recall_tags_match: str = "any",
    verbose: bool = False,
) -> EntelechyLangGraphConfig:
    """Configure Entelechy connection and default settings.

    Args:
        entelechy_api_url: Entelechy API URL (default: production).
        api_key: API key. Falls back to ENTELECHY_API_KEY env var.
        budget: Default recall budget (low/mid/high).
        max_tokens: Default max tokens for recall.
        tags: Default tags for retain operations.
        recall_tags: Default tags to filter recall/search.
        recall_tags_match: Tag matching mode.
        verbose: Enable verbose logging.

    Returns:
        The configured EntelechyLangGraphConfig.
    """
    global _global_config

    resolved_url = entelechy_api_url or DEFAULT_ENTELECHY_API_URL
    resolved_key = api_key or os.environ.get(ENTELECHY_API_KEY_ENV)

    _global_config = EntelechyLangGraphConfig(
        entelechy_api_url=resolved_url,
        api_key=resolved_key,
        budget=budget,
        max_tokens=max_tokens,
        tags=tags,
        recall_tags=recall_tags,
        recall_tags_match=recall_tags_match,
        verbose=verbose,
    )

    return _global_config


def get_config() -> Optional[EntelechyLangGraphConfig]:
    """Get the current global configuration."""
    return _global_config


def reset_config() -> None:
    """Reset global configuration to None."""
    global _global_config
    _global_config = None
