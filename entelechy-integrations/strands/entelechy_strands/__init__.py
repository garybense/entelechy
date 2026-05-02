"""Entelechy-Strands: Persistent memory tools for AI agents.

Provides Entelechy-backed tool functions for Strands agents,
giving them long-term memory via retain, recall, and reflect tools.

Basic usage::

    from strands import Agent
    from entelechy_strands import create_entelechy_tools

    tools = create_entelechy_tools(
        bank_id="user-123",
        entelechy_api_url="http://localhost:8888",
    )

    agent = Agent(tools=tools)
    agent("Remember that I prefer dark mode")
"""

from .config import (
    EntelechyStrandsConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import EntelechyError
from .tools import create_entelechy_tools, memory_instructions

__version__ = "0.1.0"

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "EntelechyStrandsConfig",
    "EntelechyError",
    "create_entelechy_tools",
    "memory_instructions",
]
