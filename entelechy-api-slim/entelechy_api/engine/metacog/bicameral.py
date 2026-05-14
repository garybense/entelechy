"""commune / listen — bicameral architecture via shared Hindsight substrate.

Channels are banks with the reserved `channel:` bank_id prefix. commune
retains a thought into the channel bank with from/to tags; listen recalls
from the channel bank, filtered by recipient. Received thoughts auto-feed
the receiver's SRL reconstruction as transient inputs without polluting
the receiver's own bank — embedding-space purity preserved.

No dedicated channels table for the MVP. Schema validation, ack cursors,
and guaranteed-delivery semantics can be added later by promoting channel
bookkeeping into a real table; the public API of commune/listen will not
change.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .state import record_state

logger = logging.getLogger(__name__)

CHANNEL_BANK_PREFIX = "channel:"


def channel_bank_id(channel: str) -> str:
    """Canonical bank id for a named channel."""
    if channel.startswith(CHANNEL_BANK_PREFIX):
        return channel
    return f"{CHANNEL_BANK_PREFIX}{channel}"


async def commune(
    *,
    engine: Any,
    channel: str,
    from_bank: str,
    to_bank: str,
    thought: str,
    request_context: Any,
    schema: dict | None = None,
) -> dict[str, Any]:
    """Send a thought into a channel bank.

    Optional `schema` validates the payload (json-schema-style dict). When
    provided, only thoughts that pass validation are retained.
    """
    cb = channel_bank_id(channel)
    if schema is not None:
        try:
            _validate_against_schema(thought, schema)
        except ValueError as exc:
            return {"status": "rejected", "error": str(exc), "channel": channel}

    try:
        await engine.create_bank(
            bank_id=cb,
            mission=f"Bicameral channel: {channel}",
            request_context=request_context,
        )
    except Exception:
        # Bank already exists (or create_bank raised) — proceed; retain will surface real errors
        pass

    tags = [
        "metacog:commune",
        f"channel:{channel}",
        f"from:{from_bank}",
        f"to:{to_bank}",
    ]
    try:
        memory_ids = await engine.retain_async(
            bank_id=cb,
            content=thought,
            context=f"commune from={from_bank} to={to_bank} | tags=[{', '.join(tags)}]",
            request_context=request_context,
        )
    except Exception as exc:
        logger.warning("[commune] retain failed: %s", exc)
        return {"status": "error", "error": str(exc)}

    msg_id = memory_ids[0] if memory_ids else None
    state = {"channel": channel, "from": from_bank, "to": to_bank, "thought_len": len(thought)}
    await record_state(bank_id=from_bank, tool_name="commune", state_data=state, memory_unit_id=msg_id)
    return {
        "status": "sent",
        "channel": channel,
        "channel_bank_id": cb,
        "from_bank": from_bank,
        "to_bank": to_bank,
        "message_id": msg_id,
    }


async def listen(
    *,
    engine: Any,
    channel: str,
    self_bank: str,
    request_context: Any,
    after_id: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Recall from a channel bank, filtered to messages addressed to self.

    Returned messages auto-feed the receiver's SRL on subsequent calls via
    the receiver's metacog_state — caller does not need to opt in. If the
    caller wants persistent integration, it can call retain_async on its
    own bank with the message text.
    """
    cb = channel_bank_id(channel)
    try:
        result = await engine.recall_async(
            bank_id=cb,
            query=f"messages to {self_bank}",
            max_tokens=2048,
            tags=[f"to:{self_bank}", "to:*"],
            tags_match="any",
            request_context=request_context,
            _quiet=True,
        )
    except Exception as exc:
        logger.warning("[listen] recall failed: %s", exc)
        return {"status": "error", "error": str(exc), "channel": channel, "messages": []}

    payload = result.model_dump() if hasattr(result, "model_dump") else (result or {})
    raw = payload.get("memories") or payload.get("results") or []
    messages = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if after_id and item.get("id") == after_id:
            messages = []  # cursor — drop everything up to and including after_id
            continue
        messages.append(
            {
                "id": item.get("id"),
                "from_bank": _extract_from(item),
                "thought": item.get("text"),
                "tags": item.get("tags") or [],
                "created_at": item.get("event_date") or item.get("mentioned_at"),
            }
        )
        if len(messages) >= limit:
            break

    state = {"channel": channel, "received_count": len(messages)}
    await record_state(bank_id=self_bank, tool_name="listen", state_data=state)
    return {
        "status": "received",
        "channel": channel,
        "channel_bank_id": cb,
        "self_bank": self_bank,
        "messages": messages,
    }


# --- internals ---


def _extract_from(item: dict) -> str | None:
    for tag in item.get("tags") or []:
        if isinstance(tag, str) and tag.startswith("from:"):
            return tag[len("from:") :]
    return None


def _validate_against_schema(payload: str, schema: dict) -> None:
    """Minimal schema check. Validates that JSON-decoded payload has all
    required keys named in schema['required']. No type checking — kept
    deliberately small; richer validation can adopt jsonschema later.
    """
    required = schema.get("required") or []
    if not required:
        return
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"payload is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("payload must be a JSON object")
    missing = [k for k in required if k not in parsed]
    if missing:
        raise ValueError(f"payload missing required keys: {missing}")
