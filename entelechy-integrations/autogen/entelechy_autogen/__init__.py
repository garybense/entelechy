"""Entelechy-AutoGen: Persistent memory tools for AutoGen agents.

Provides ``FunctionTool`` instances that give AutoGen agents long-term memory
via Entelechy's retain/recall/reflect APIs.

Basic usage::

    from entelechy_client import Entelechy
    from entelechy_autogen import create_entelechy_tools

    client = Entelechy(base_url="http://localhost:8888")
    tools = create_entelechy_tools(client=client, bank_id="user-123")

    # Use with an AutoGen AssistantAgent
    agent = AssistantAgent(name="assistant", model_client=model, tools=tools)
"""

from .config import (
    EntelechyAutoGenConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import EntelechyError
from .tools import create_entelechy_tools

__version__ = "0.1.0"

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "EntelechyAutoGenConfig",
    "EntelechyError",
    "create_entelechy_tools",
]
