"""Lightweight per-bank metacog primitive history.

Process-local ring buffer keyed by (bank_id, tool_name). SRL reconstructor
reads this to populate `recent_metacog_state` on every reconstruction.

Persistence: each record is also retained as a memory_unit tagged
`metacog:state:{tool_name}` so it survives process restarts via the
existing memory store. The in-memory buffer is the hot path.

This deliberately avoids a dedicated metacog_state table — a richer
schema can land later without breaking callers, since the public API is
just `record_state` / `get_recent_state`.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

_HISTORY_LIMIT = 50

_history: dict[tuple[str, str], deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=_HISTORY_LIMIT))
_history_lock = asyncio.Lock()


async def record_state(
    *,
    bank_id: str,
    tool_name: str,
    state_data: dict[str, Any],
    memory_unit_id: str | None = None,
) -> dict[str, Any]:
    """Append a state record to the per-bank ring buffer."""
    record = {
        "bank_id": bank_id,
        "tool_name": tool_name,
        "state_data": state_data,
        "memory_unit_id": memory_unit_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    async with _history_lock:
        _history[(bank_id, tool_name)].append(record)
    return record


async def get_recent_state(
    bank_id: str,
    *,
    tool_names: list[str] | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Return the most-recent metacog state records for a bank.

    If `tool_names` is None, returns records across ALL primitives merged
    in reverse-chronological order. Limit applies to the merged result.
    """
    async with _history_lock:
        merged: list[dict[str, Any]] = []
        if tool_names is None:
            for (bank, _tool), records in _history.items():
                if bank == bank_id:
                    merged.extend(records)
        else:
            for tool in tool_names:
                merged.extend(_history.get((bank_id, tool), ()))
        merged.sort(key=lambda r: r["created_at"], reverse=True)
        return merged[:limit]


async def clear_state(bank_id: str) -> None:
    """Drop all in-memory state for a bank. Used by tests."""
    async with _history_lock:
        for key in list(_history.keys()):
            if key[0] == bank_id:
                _history.pop(key, None)
