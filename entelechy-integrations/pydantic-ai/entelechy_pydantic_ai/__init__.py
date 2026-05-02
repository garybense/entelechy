"""Entelechy-Pydantic AI: Persistent memory tools for AI agents.

Provides Entelechy-backed tools and instructions for Pydantic AI agents,
giving them long-term memory across runs.

Basic usage::

    from entelechy_client import Entelechy
    from entelechy_pydantic_ai import create_entelechy_tools, memory_instructions
    from pydantic_ai import Agent

    client = Entelechy(base_url="http://localhost:8888")

    agent = Agent(
        "openai:gpt-4o",
        tools=create_entelechy_tools(client=client, bank_id="user-123"),
        instructions=[memory_instructions(client=client, bank_id="user-123")],
    )

    result = await agent.run("What do you remember about my preferences?")
"""

from .config import (
    EntelechyPydanticAIConfig,
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
    "EntelechyPydanticAIConfig",
    "EntelechyError",
    "create_entelechy_tools",
    "memory_instructions",
]
