"""Entelechy-Agno: Persistent memory tools for AI agents.

Provides a Entelechy-backed Toolkit for Agno agents,
giving them long-term memory via retain, recall, and reflect tools.

Basic usage::

    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from entelechy_agno import EntelechyTools, memory_instructions

    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[EntelechyTools(
            bank_id="user-123",
            entelechy_api_url="http://localhost:8888",
        )],
        instructions=[memory_instructions(
            bank_id="user-123",
            entelechy_api_url="http://localhost:8888",
        )],
    )

    agent.print_response("What do you remember about my preferences?")
"""

from .config import (
    EntelechyAgnoConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import EntelechyError
from .tools import EntelechyTools, memory_instructions

__version__ = "0.1.0"

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "EntelechyAgnoConfig",
    "EntelechyError",
    "EntelechyTools",
    "memory_instructions",
]
