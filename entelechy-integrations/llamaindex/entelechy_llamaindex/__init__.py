"""Entelechy memory integration for LlamaIndex agents.

Provides two complementary patterns:

- **Tools** (``EntelechyToolSpec``, ``create_entelechy_tools``):
  Agent-driven memory via LlamaIndex's ``BaseToolSpec``.
  The agent decides when to retain/recall/reflect.

- **Memory** (``EntelechyMemory``):
  Automatic memory via LlamaIndex's ``BaseMemory`` interface.
  Messages are stored on ``put()`` and recalled on ``get()``.

Usage::

    from entelechy_llamaindex import EntelechyToolSpec, create_entelechy_tools
    from entelechy_llamaindex import EntelechyMemory
"""

from .config import (
    EntelechyLlamaIndexConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import EntelechyError
from .memory import EntelechyMemory
from .tools import EntelechyToolSpec, create_entelechy_tools

__version__ = "0.1.2"

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "EntelechyLlamaIndexConfig",
    "EntelechyError",
    "EntelechyToolSpec",
    "create_entelechy_tools",
    "EntelechyMemory",
]
