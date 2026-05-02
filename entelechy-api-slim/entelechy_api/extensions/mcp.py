"""MCP Extension for registering additional MCP tools.

This extension allows external packages (like entelechy-cloud) to register
additional MCP tools on the Entelechy MCP server.

Example:
    ENTELECHY_API_MCP_EXTENSION=entelechy_cloud.extensions:CloudMCPExtension
"""

import logging
from abc import abstractmethod

from fastmcp import FastMCP

from entelechy_api import MemoryEngine
from entelechy_api.extensions.base import Extension

logger = logging.getLogger(__name__)


class MCPExtension(Extension):
    """Base class for MCP extensions that register additional tools.

    Subclass this to add MCP tools in extension packages.

    Example:
        class CloudMCPExtension(MCPExtension):
            def register_tools(self, mcp: FastMCP, memory: MemoryEngine) -> None:
                @mcp.tool()
                async def my_custom_tool(query: str) -> str:
                    return "result"
    """

    @abstractmethod
    def register_tools(self, mcp: FastMCP, memory: MemoryEngine) -> None:
        """Register additional MCP tools.

        Args:
            mcp: FastMCP server instance to register tools on
            memory: MemoryEngine instance for accessing memory operations
        """
        pass
