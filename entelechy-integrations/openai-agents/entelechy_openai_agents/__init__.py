"""Entelechy-OpenAI-Agents: Persistent memory tools for OpenAI Agents SDK.

Provides ``FunctionTool`` instances that give OpenAI agents long-term memory
via Entelechy's retain/recall/reflect APIs.

Basic usage::

    from entelechy_client import Entelechy
    from entelechy_openai_agents import create_entelechy_tools

    client = Entelechy(base_url="http://localhost:8888")
    tools = create_entelechy_tools(client=client, bank_id="user-123")

    agent = Agent(name="assistant", tools=tools)
"""

from ._version import __version__
from .config import (
    EntelechyOpenAIAgentsConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import EntelechyError
from .tools import create_entelechy_tools, memory_instructions

__all__ = [
    "__version__",
    "configure",
    "get_config",
    "reset_config",
    "EntelechyOpenAIAgentsConfig",
    "EntelechyError",
    "create_entelechy_tools",
    "memory_instructions",
]
