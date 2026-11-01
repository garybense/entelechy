"""The metacog primitives are exposed as MCP tools with real schemas."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import FastMCP

from entelechy_api.engine.metacog.mcp_tools import register_metacog_tools
from entelechy_api.mcp_tools import METACOG_TOOL_NAMES, MCPToolsConfig, _ALL_TOOLS


def _config(multi: bool) -> MCPToolsConfig:
    return MCPToolsConfig(bank_id_resolver=lambda: "session-bank", include_bank_id_param=multi)


async def _tools(multi: bool):
    mcp = FastMCP("t")
    register_metacog_tools(mcp, object(), _config(multi))
    return mcp, {t.name: t for t in await mcp.list_tools()}


def test_all_names_are_enabled_by_default():
    assert set(METACOG_TOOL_NAMES) <= _ALL_TOOLS
    assert len(METACOG_TOOL_NAMES) == 12


@pytest.mark.asyncio
async def test_all_twelve_tools_are_listed_with_schemas():
    _, tools = await _tools(multi=True)
    assert set(tools) == set(METACOG_TOOL_NAMES)
    props = tools["ritual"].parameters["properties"]
    assert set(props) == {"threshold", "steps", "result", "bank_id"}
    assert tools["ritual"].parameters["required"] == ["threshold", "steps", "result"]
    assert "bank_id" not in (await _tools(multi=False))[1]["ritual"].parameters["properties"]


@pytest.mark.asyncio
async def test_call_routes_to_primitive_with_resolved_bank():
    mcp, _ = await _tools(multi=False)
    with patch("entelechy_api.engine.metacog.primitives.become", new=AsyncMock(return_value={"ok": True})) as m:
        res = await mcp.call_tool("become", {"name": "n", "lens": "l", "environment": "e"})
    assert json.loads(res.content[0].text) == {"ok": True}
    assert m.await_args.kwargs["bank_id"] == "session-bank"
    assert m.await_args.kwargs["lens"] == "l"


@pytest.mark.asyncio
async def test_commune_and_listen_use_bank_as_sender_and_receiver():
    mcp, _ = await _tools(multi=True)
    with patch("entelechy_api.engine.metacog.bicameral.commune", new=AsyncMock(return_value={})) as c:
        await mcp.call_tool("commune", {"channel": "c", "to_bank": "b2", "thought": "hi", "bank_id": "b1"})
    assert c.await_args.kwargs["from_bank"] == "b1" and c.await_args.kwargs["to_bank"] == "b2"
    with patch("entelechy_api.engine.metacog.bicameral.listen", new=AsyncMock(return_value={})) as l:
        await mcp.call_tool("listen", {"channel": "c", "bank_id": "b2"})
    assert l.await_args.kwargs["self_bank"] == "b2"
