"""MCP tools for the metacog cycle: feel, drugs, become, name, ritual, molt, compass,
commune, listen and the identity-preset tools.

Each tool resolves its bank like the soul tools do: a ``bank_id`` argument when the
server runs multi-bank, otherwise the session bank. Every call goes through the same
request context (tenant auth, ownership validation) as the other MCP tools.
"""

from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastmcp import FastMCP

from entelechy_api.engine.memory_engine import MemoryEngine
from entelechy_api.extensions import OperationValidationError
from entelechy_api.mcp_tools import METACOG_TOOL_NAMES, MCPToolsConfig, _get_request_context  # noqa: F401

from . import bicameral, presets, primitives, soul_ops

logger = logging.getLogger(__name__)

def _dump(result: Any) -> str:
    if hasattr(result, "model_dump"):
        result = result.model_dump(mode="json")
    return json.dumps(result, default=str)


def register_metacog_tools(mcp: FastMCP, memory: MemoryEngine, config: MCPToolsConfig, only: set[str] | None = None) -> None:
    """Register the metacog tools (all of them, or the subset named in ``only``)."""

    def add(name: str, doc: str, params: list[tuple[str, Any, Any]], call: Callable[..., Awaitable[Any]]) -> None:
        """Register one tool. ``params`` is (name, annotation, default) with
        ``inspect.Parameter.empty`` marking required ones; ``call`` receives the keyword
        arguments plus ``bank_id`` and ``request_context``."""
        if only is not None and name not in only:
            return

        async def tool(**kwargs: Any) -> str:
            try:
                bank_id = kwargs.pop("bank_id", None) or config.bank_id_resolver()
                if bank_id is None:
                    return json.dumps({"error": "No bank_id configured"})
                result = await call(bank_id=bank_id, request_context=_get_request_context(config), **kwargs)
                return _dump(result)
            except OperationValidationError as e:
                logger.warning("Operation rejected: %s", e)
                return json.dumps({"error": str(e)})
            except Exception as e:
                logger.error("Error in %s: %s", name, e, exc_info=True)
                return json.dumps({"error": str(e)})

        parameters = [
            inspect.Parameter(
                pname,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=annotation,
                default=default,
            )
            for pname, annotation, default in params
        ]
        if config.include_bank_id_param:
            parameters.append(
                inspect.Parameter(
                    "bank_id", inspect.Parameter.KEYWORD_ONLY, annotation=str | None, default=None
                )
            )
        # FastMCP builds the tool schema from the function signature.
        tool.__signature__ = inspect.Signature(parameters, return_annotation=str)  # type: ignore[attr-defined]
        tool.__annotations__ = {p.name: p.annotation for p in parameters} | {"return": str}
        tool.__name__ = name
        tool.__doc__ = doc
        mcp.tool(name=name)(tool)

    R = inspect.Parameter.empty

    add(
        "feel",
        "Record a pre-verbal felt sense. `somewhere` is where in the body or situation it sits, "
        "`quality` is what it is like, `sigil` is an optional glyph. Returns similar past felt senses.",
        [("somewhere", str, R), ("quality", str, R), ("sigil", str, "🌫️")],
        lambda **kw: primitives.feel(engine=memory, **kw),
    )
    add(
        "drugs",
        "Alter the cognitive substrate: name the `substance` and the `method`. Retains the alteration "
        "and sets a transient directive that the next call to this tool replaces.",
        [("substance", str, R), ("method", str, R)],
        lambda **kw: primitives.drugs(engine=memory, **kw),
    )
    add(
        "become",
        "Install an identity or perspective: `name`, the `lens` it looks through, and the `environment` "
        "it lives in. Retains the shift and creates a directive for it.",
        [("name", str, R), ("lens", str, R), ("environment", str, R)],
        lambda **kw: primitives.become(engine=memory, **kw),
    )
    add(
        "name",
        "Performative naming: give the `unnamed` thing its `named` name and the `power` the name carries. "
        "Creates a high-priority directive and a mental model.",
        [("unnamed", str, R), ("named", str, R), ("power", str, R)],
        lambda **kw: primitives.name_(engine=memory, **kw),
    )
    add(
        "ritual",
        "Run an irreversible ritual: a `threshold` crossed, ordered `steps`, and the `result` that takes hold.",
        [("threshold", str, R), ("steps", list[str], R), ("result", str, R)],
        lambda **kw: primitives.ritual(engine=memory, **kw),
    )
    add(
        "molt",
        "Assemble molt material for a `catalyst`: the current soul, recent metacog state and the SRL gap.",
        [("catalyst", str, R)],
        lambda **kw: soul_ops.molt(engine=memory, **kw),
    )
    add(
        "compass",
        "Detect drift for a `bearing`: compares the reconstructed state vector with the encoded soul checkpoint "
        "and reports a drift signal against `drift_threshold`.",
        [("bearing", str, R), ("drift_threshold", float, 0.5)],
        lambda **kw: soul_ops.compass(engine=memory, **kw),
    )

    async def _commune(bank_id: str, request_context: Any, **kw: Any) -> Any:
        return await bicameral.commune(engine=memory, from_bank=bank_id, request_context=request_context, **kw)

    add(
        "commune",
        "Send a `thought` from this bank to bank `to_bank` through a named `channel`. Optional JSON-schema "
        "`schema` validates the thought; only thoughts that pass are retained.",
        [("channel", str, R), ("to_bank", str, R), ("thought", str, R), ("schema", dict | None, None)],
        _commune,
    )

    async def _listen(bank_id: str, request_context: Any, **kw: Any) -> Any:
        return await bicameral.listen(engine=memory, self_bank=bank_id, request_context=request_context, **kw)

    add(
        "listen",
        "Read messages in a named `channel` that are addressed to this bank, optionally after message id "
        "`after_id`, up to `limit`.",
        [("channel", str, R), ("after_id", str | None, None), ("limit", int, 20)],
        _listen,
    )
    add(
        "save_identity_preset",
        "Save a named identity preset: `soul_encoding` fields plus optional `disposition_modifiers`.",
        [
            ("preset_name", str, R),
            ("soul_encoding", dict[str, str], R),
            ("disposition_modifiers", dict[str, int] | None, None),
        ],
        lambda **kw: presets.save_preset(engine=memory, **kw),
    )
    add(
        "list_identity_presets",
        "List the identity presets saved on this bank.",
        [],
        lambda **kw: presets.list_presets(engine=memory, **kw),
    )
    add(
        "hydrate_preset",
        "Apply a saved identity preset to this bank (encodes its soul and updates the bank).",
        [("preset_name", str, R)],
        lambda **kw: presets.hydrate_preset(engine=memory, **kw),
    )
