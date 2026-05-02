"""Shared Entelechy client resolution logic."""

from importlib import metadata
from typing import Any, Optional

from entelechy_client import Entelechy

from .config import get_config
from .errors import EntelechyError

try:
    _VERSION = metadata.version("entelechy-ag2")
except metadata.PackageNotFoundError:
    _VERSION = "0.0.0"
_USER_AGENT = f"entelechy-ag2/{_VERSION}"


def resolve_client(
    client: Optional[Entelechy],
    entelechy_api_url: Optional[str],
    api_key: Optional[str],
) -> Entelechy:
    """Resolve a Entelechy client from explicit args or global config."""
    if client is not None:
        return client

    config = get_config()
    url = entelechy_api_url or (config.entelechy_api_url if config else None)
    key = api_key or (config.api_key if config else None)

    if url is None:
        raise EntelechyError(
            "No Entelechy API URL configured. Pass client= or entelechy_api_url=, or call configure() first."
        )

    kwargs: dict[str, Any] = {"base_url": url, "timeout": 30.0, "user_agent": _USER_AGENT}
    if key:
        kwargs["api_key"] = key
    return Entelechy(**kwargs)
