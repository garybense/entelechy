"""Entelechy-CrewAI: Persistent memory for AI agent crews.

Provides a Entelechy-backed Storage implementation for CrewAI's
ExternalMemory system, giving your crews long-term memory across runs.

Basic usage::

    from entelechy_crewai import configure, EntelechyStorage
    from crewai.memory.external.external_memory import ExternalMemory
    from crewai import Crew

    configure(entelechy_api_url="http://localhost:8888")

    crew = Crew(
        agents=[...],
        tasks=[...],
        external_memory=ExternalMemory(
            storage=EntelechyStorage(bank_id="my-crew")
        ),
    )

Per-agent banks::

    storage = EntelechyStorage(
        bank_id="crew-shared",
        per_agent_banks=True,
    )
"""

from .config import (
    EntelechyCrewAIConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import EntelechyError
from .storage import EntelechyStorage
from .tools import EntelechyReflectTool

__version__ = "0.1.0"

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "EntelechyCrewAIConfig",
    "EntelechyStorage",
    "EntelechyReflectTool",
    "EntelechyError",
]
