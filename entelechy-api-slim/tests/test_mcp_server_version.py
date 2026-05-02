"""Tests for MCP server identity reported via serverInfo."""

from unittest.mock import MagicMock

from entelechy_api import __version__ as ENTELECHY_VERSION
from entelechy_api.api.mcp import create_mcp_server


def test_mcp_server_reports_entelechy_version():
    """serverInfo.version should be Entelechy's version, not the FastMCP library version."""
    memory = MagicMock()
    server = create_mcp_server(memory, multi_bank=True)
    assert server.version == ENTELECHY_VERSION
