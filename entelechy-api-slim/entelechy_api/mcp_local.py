"""
Local MCP server entry point for use with Claude Code (HTTP transport).

This is a thin wrapper around the main entelechy-api server that pre-configures
sensible defaults for local use (embedded PostgreSQL via pg0, warning log level).

The full API runs on localhost:8888. Configure Claude Code's MCP settings:
    claude mcp add --transport http entelechy http://localhost:8888/mcp/

Or pinned to a specific bank (single-bank mode):
    claude mcp add --transport http entelechy http://localhost:8888/mcp/default/

Run with:
    entelechy-local-mcp

Or with uvx:
    uvx entelechy-api@latest entelechy-local-mcp

Environment variables:
    ENTELECHY_API_LLM_API_KEY: Required. API key for LLM provider.
    ENTELECHY_API_LLM_PROVIDER: Optional. LLM provider (default: "openai").
    ENTELECHY_API_LLM_MODEL: Optional. LLM model (default: "gpt-4o-mini").
    ENTELECHY_API_DATABASE_URL: Optional. Override database URL (default: pg0://entelechy-mcp).
"""

import os


def main() -> None:
    """Start the Entelechy API server with local defaults."""
    # Set local defaults (only if not already configured by the user)
    os.environ.setdefault("ENTELECHY_API_DATABASE_URL", "pg0://entelechy-mcp")

    from entelechy_api.main import main as api_main

    api_main()


if __name__ == "__main__":
    main()
