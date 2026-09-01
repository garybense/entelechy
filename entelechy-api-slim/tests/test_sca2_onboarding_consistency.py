"""Onboarding payloads must only reference tools that are actually registered.

Guards against the bug class where MCP handshake instructions advertise tools
(e.g. metacog primitives) that no code registers — connecting agents then call
tools that don't exist as their first action.
"""

import re

from entelechy_api.api.mcp import _SERVER_INSTRUCTIONS, _START_HERE_PAYLOAD
from entelechy_api.mcp_tools import _ALL_TOOLS

# Non-tool vocabulary that may legitimately appear in onboarding text.
_ALLOWED_NON_TOOLS = {
    "start_here",  # registered separately in _register_onboarding
}

_TOOL_TOKEN = re.compile(r"`([a-z_]{3,})`|\b([a-z_]+_[a-z_]+)\b")


def _referenced_tool_names(text: str) -> set[str]:
    """Extract snake_case tokens that look like tool references."""
    names: set[str] = set()
    for backticked, bare in _TOOL_TOKEN.findall(text):
        token = backticked or bare
        # Only flag tokens that collide with tool-name shape: contain an
        # underscore or are known single-word tools.
        if "_" in token or token in {"retain", "recall", "reflect"}:
            names.add(token)
    return names


def _flatten(payload) -> str:
    if isinstance(payload, dict):
        return " ".join(_flatten(v) for v in list(payload.keys()) + list(payload.values()))
    if isinstance(payload, list):
        return " ".join(_flatten(v) for v in payload)
    return str(payload)


def test_server_instructions_reference_only_registered_tools():
    referenced = _referenced_tool_names(_SERVER_INSTRUCTIONS)
    unknown = referenced - _ALL_TOOLS - _ALLOWED_NON_TOOLS
    # Filter to plausible tool names: those matching a registered tool prefix
    # or verbs agents would call. Anything left is an advertised-but-missing tool.
    suspicious = {
        t for t in unknown if any(t.startswith(p) for p in ("create_", "get_", "list_", "delete_", "encode_", "sync_"))
    }
    assert not suspicious, f"_SERVER_INSTRUCTIONS advertises unregistered tools: {sorted(suspicious)}"


def test_start_here_payload_references_only_registered_tools():
    text = _flatten(_START_HERE_PAYLOAD)
    referenced = _referenced_tool_names(text)
    unknown = referenced - _ALL_TOOLS - _ALLOWED_NON_TOOLS
    suspicious = {
        t for t in unknown if any(t.startswith(p) for p in ("create_", "get_", "list_", "delete_", "encode_", "sync_"))
    }
    assert not suspicious, f"start_here payload advertises unregistered tools: {sorted(suspicious)}"


def test_metacog_vocabulary_absent_from_onboarding():
    """Metacog features are intentionally hidden; onboarding must not leak them."""
    banned = ["feel(", "drugs", "molt", "compass", "commune", "sigil", "soul", "SRL", "MWPM", "bicameral", "ritual"]
    text = _SERVER_INSTRUCTIONS + _flatten(_START_HERE_PAYLOAD)
    leaked = [w for w in banned if w in text]
    assert not leaked, f"Onboarding leaks hidden metacog vocabulary: {leaked}"
