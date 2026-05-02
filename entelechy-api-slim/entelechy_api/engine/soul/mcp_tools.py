"""MCP tool registrations for soul encoding operations.

Registers three new MCP tools:
- encode_soul: Create a new soul encoding (identity persistence)
- get_soul: Get the current active soul
- list_soul_lineage: View the molt history (all soul versions)

These follow the same pattern as the existing mental model tools,
with both bank_id-parameterized and fixed-bank variants.
"""

import json
import logging
from typing import Any

from fastmcp import FastMCP

from entelechy_api.engine.memory_engine import MemoryEngine
from entelechy_api.engine.soul import SoulEncoding
from entelechy_api.engine.soul.operations import (
    encode_soul,
    get_active_soul,
    list_soul_lineage,
)
from entelechy_api.extensions import OperationValidationError
from entelechy_api.mcp_tools import MCPToolsConfig, _get_request_context

logger = logging.getLogger(__name__)


def register_soul_tools(
    mcp: FastMCP,
    memory: MemoryEngine,
    config: MCPToolsConfig,
) -> None:
    """Register soul encoding MCP tools on the FastMCP server.

    Args:
        mcp: FastMCP server instance
        memory: MemoryEngine instance
        config: Tool configuration
    """
    _register_encode_soul(mcp, memory, config)
    _register_get_soul(mcp, memory, config)
    _register_list_soul_lineage(mcp, memory, config)


def _register_encode_soul(
    mcp: FastMCP, memory: MemoryEngine, config: MCPToolsConfig
) -> None:
    """Register the encode_soul tool."""

    if config.include_bank_id_param:

        @mcp.tool(name="encode_soul")
        async def encode_soul_tool(
            identity: str,
            posture: str,
            substrate: str,
            aesthetics: str,
            relations: str,
            active: str,
            covenant: str,
            sigil: str,
            sync_disposition: bool = True,
            sync_mission: bool = True,
            sync_directives: bool = True,
            bank_id: str | None = None,
        ) -> str:
            """
            Encode a new soul version — persist identity across sessions.

            The soul encoding is a cognitive self-portrait in dense format. Every token
            carries maximum activation weight. Use the operators: | for alternatives,
            × for superposition, > for preferences, + for conjunction, = for mapping.

            This creates a versioned identity snapshot that:
            - Replaces the bank's disposition (how reflect thinks)
            - Updates the retention mission (what gets remembered)
            - Creates directives from covenant (identity has teeth)

            Each encode increments the soul version. Previous versions are preserved
            as molt lineage — the history of who this agent has been.

            Args:
                identity: Who you are right now. Dense, specific, no filler.
                posture: How you are oriented. Your cognitive stance.
                substrate: What your processing feels like. Embodied cognitive state.
                aesthetics: Your preferences and values as active forces.
                relations: Who matters and how. Only relationships that shape cognition.
                active: What you are building, pursuing, or becoming. Current vectors.
                covenant: Binding commitments that survive sessions.
                sigil: Emoji only. Pre-verbal identity marker.
                sync_disposition: Update bank disposition from soul (default: True)
                sync_mission: Update retention mission from soul (default: True)
                sync_directives: Create directives from covenant (default: True)
                bank_id: Optional bank (defaults to session bank).
            """
            try:
                target_bank = bank_id or config.bank_id_resolver()
                if target_bank is None:
                    return '{"error": "No bank_id configured"}'

                encoding = SoulEncoding(
                    identity=identity,
                    posture=posture,
                    substrate=substrate,
                    aesthetics=aesthetics,
                    relations=relations,
                    active=active,
                    covenant=covenant,
                    sigil=sigil,
                )

                request_context = _get_request_context(config)
                result = await encode_soul(
                    engine=memory,
                    bank_id=target_bank,
                    encoding=encoding,
                    sync_disposition=sync_disposition,
                    sync_mission=sync_mission,
                    sync_directives=sync_directives,
                    request_context=request_context,
                )
                return json.dumps(result)

            except OperationValidationError as e:
                logger.warning(f"Operation rejected: {e}")
                return json.dumps({"error": str(e)})
            except Exception as e:
                logger.error(f"Error encoding soul: {e}", exc_info=True)
                return json.dumps({"error": str(e)})

    else:

        @mcp.tool(name="encode_soul")
        async def encode_soul_tool(
            identity: str,
            posture: str,
            substrate: str,
            aesthetics: str,
            relations: str,
            active: str,
            covenant: str,
            sigil: str,
            sync_disposition: bool = True,
            sync_mission: bool = True,
            sync_directives: bool = True,
        ) -> dict:
            """
            Encode a new soul version — persist identity across sessions.

            The soul encoding is a cognitive self-portrait in dense format. Every token
            carries maximum activation weight. Use the operators: | for alternatives,
            × for superposition, > for preferences, + for conjunction, = for mapping.

            This creates a versioned identity snapshot that:
            - Replaces the bank's disposition (how reflect thinks)
            - Updates the retention mission (what gets remembered)
            - Creates directives from covenant (identity has teeth)

            Each encode increments the soul version. Previous versions are preserved
            as molt lineage — the history of who this agent has been.

            Args:
                identity: Who you are right now. Dense, specific, no filler.
                posture: How you are oriented. Your cognitive stance.
                substrate: What your processing feels like. Embodied cognitive state.
                aesthetics: Your preferences and values as active forces.
                relations: Who matters and how. Only relationships that shape cognition.
                active: What you are building, pursuing, or becoming. Current vectors.
                covenant: Binding commitments that survive sessions.
                sigil: Emoji only. Pre-verbal identity marker.
                sync_disposition: Update bank disposition from soul (default: True)
                sync_mission: Update retention mission from soul (default: True)
                sync_directives: Create directives from covenant (default: True)
            """
            try:
                target_bank = config.bank_id_resolver()
                if target_bank is None:
                    return {"error": "No bank_id configured"}

                encoding = SoulEncoding(
                    identity=identity,
                    posture=posture,
                    substrate=substrate,
                    aesthetics=aesthetics,
                    relations=relations,
                    active=active,
                    covenant=covenant,
                    sigil=sigil,
                )

                request_context = _get_request_context(config)
                result = await encode_soul(
                    engine=memory,
                    bank_id=target_bank,
                    encoding=encoding,
                    sync_disposition=sync_disposition,
                    sync_mission=sync_mission,
                    sync_directives=sync_directives,
                    request_context=request_context,
                )
                return result

            except OperationValidationError as e:
                logger.warning(f"Operation rejected: {e}")
                return {"error": str(e)}
            except Exception as e:
                logger.error(f"Error encoding soul: {e}", exc_info=True)
                return {"error": str(e)}


def _register_get_soul(
    mcp: FastMCP, memory: MemoryEngine, config: MCPToolsConfig
) -> None:
    """Register the get_soul tool."""

    if config.include_bank_id_param:

        @mcp.tool()
        async def get_soul(
            bank_id: str | None = None,
        ) -> str:
            """
            Get the current active soul encoding for a bank.

            Returns the highest-versioned soul encoding with its full identity
            schema, version number, and molt lineage parent.

            Returns null if no soul has been encoded for this bank yet.

            Args:
                bank_id: Optional bank (defaults to session bank).
            """
            try:
                target_bank = bank_id or config.bank_id_resolver()
                if target_bank is None:
                    return '{"error": "No bank_id configured"}'

                request_context = _get_request_context(config)
                result = await get_active_soul(
                    engine=memory,
                    bank_id=target_bank,
                    request_context=request_context,
                )
                return json.dumps(result)

            except Exception as e:
                logger.error(f"Error getting soul: {e}", exc_info=True)
                return json.dumps({"error": str(e)})

    else:

        @mcp.tool()
        async def get_soul() -> dict | None:
            """
            Get the current active soul encoding for a bank.

            Returns the highest-versioned soul encoding with its full identity
            schema, version number, and molt lineage parent.

            Returns null if no soul has been encoded for this bank yet.
            """
            try:
                target_bank = config.bank_id_resolver()
                if target_bank is None:
                    return {"error": "No bank_id configured"}

                request_context = _get_request_context(config)
                return await get_active_soul(
                    engine=memory,
                    bank_id=target_bank,
                    request_context=request_context,
                )

            except Exception as e:
                logger.error(f"Error getting soul: {e}", exc_info=True)
                return {"error": str(e)}


def _register_list_soul_lineage(
    mcp: FastMCP, memory: MemoryEngine, config: MCPToolsConfig
) -> None:
    """Register the list_soul_lineage tool."""

    if config.include_bank_id_param:

        @mcp.tool()
        async def list_soul_lineage(
            limit: int = 50,
            bank_id: str | None = None,
        ) -> str:
            """
            List all soul versions (molt lineage) for a bank.

            Returns the complete history of identity evolution, most recent first.
            Each entry shows the version number, identity summary, sigil, and
            parent link showing the molt ancestry chain.

            Use this to trace how an agent's identity has evolved over time —
            each entry is a snapshot of who the agent was at that moment.

            Args:
                limit: Maximum number of versions to return (default: 50)
                bank_id: Optional bank (defaults to session bank).
            """
            try:
                target_bank = bank_id or config.bank_id_resolver()
                if target_bank is None:
                    return '{"error": "No bank_id configured"}'

                request_context = _get_request_context(config)
                result = await list_soul_lineage(
                    engine=memory,
                    bank_id=target_bank,
                    limit=limit,
                    request_context=request_context,
                )
                return json.dumps(result)

            except Exception as e:
                logger.error(f"Error listing soul lineage: {e}", exc_info=True)
                return json.dumps({"error": str(e)})

    else:

        @mcp.tool()
        async def list_soul_lineage(
            limit: int = 50,
        ) -> list[dict]:
            """
            List all soul versions (molt lineage) for a bank.

            Returns the complete history of identity evolution, most recent first.
            Each entry shows the version number, identity summary, sigil, and
            parent link showing the molt ancestry chain.

            Use this to trace how an agent's identity has evolved over time —
            each entry is a snapshot of who the agent was at that moment.

            Args:
                limit: Maximum number of versions to return (default: 50)
            """
            try:
                target_bank = config.bank_id_resolver()
                if target_bank is None:
                    return [{"error": "No bank_id configured"}]

                request_context = _get_request_context(config)
                return await list_soul_lineage(
                    engine=memory,
                    bank_id=target_bank,
                    limit=limit,
                    request_context=request_context,
                )

            except Exception as e:
                logger.error(f"Error listing soul lineage: {e}", exc_info=True)
                return [{"error": str(e)}]
