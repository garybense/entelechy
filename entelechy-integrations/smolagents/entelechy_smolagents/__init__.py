"""Entelechy-SmolAgents: Persistent memory tools for AI agents.

Provides Entelechy-backed Tool subclasses for SmolAgents agents,
giving them long-term memory via retain, recall, and reflect tools.

Basic usage::

    from smolagents import CodeAgent, HfApiModel
    from entelechy_smolagents import create_entelechy_tools

    tools = create_entelechy_tools(
        bank_id="user-123",
        entelechy_api_url="http://localhost:8888",
    )

    agent = CodeAgent(
        tools=tools,
        model=HfApiModel(),
    )

    agent.run("Remember that I prefer dark mode")
"""

from .config import (
    EntelechySmolAgentsConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import EntelechyError
from .tools import (
    EntelechyRecallTool,
    EntelechyReflectTool,
    EntelechyRetainTool,
    create_entelechy_tools,
    memory_instructions,
)

__version__ = "0.1.0"

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "EntelechySmolAgentsConfig",
    "EntelechyError",
    "EntelechyRetainTool",
    "EntelechyRecallTool",
    "EntelechyReflectTool",
    "create_entelechy_tools",
    "memory_instructions",
]
