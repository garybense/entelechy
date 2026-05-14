"""Identity presets — first-class loadable persona objects.

Persisted as mental_models with subtype='structural' and tag
`metacog:identity-preset` for the MVP. A dedicated identity_presets table
can be added later; the public API of list_presets / hydrate_preset will
not change.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


_PRESET_TAG = "metacog:identity-preset"


async def save_preset(
    *,
    engine: Any,
    bank_id: str,
    preset_name: str,
    soul_encoding: dict[str, str],
    disposition_modifiers: dict[str, int] | None = None,
    request_context: Any,
) -> dict[str, Any]:
    """Save an identity preset on a bank.

    The preset is stored as a structural mental_model whose `content`
    field is the JSON-serialized preset payload.
    """
    payload = {
        "preset_name": preset_name,
        "soul_encoding": soul_encoding,
        "disposition_modifiers": disposition_modifiers or {},
    }
    try:
        result = await engine.create_mental_model(
            bank_id=bank_id,
            name=f"preset: {preset_name}",
            source_query=f"identity-preset: {preset_name}",
            content=json.dumps(payload, indent=2),
            tags=[_PRESET_TAG, f"preset:{preset_name}"],
            request_context=request_context,
        )
    except Exception as exc:
        logger.warning("[presets] save failed: %s", exc)
        return {"status": "error", "error": str(exc)}
    return {
        "status": "saved",
        "preset_name": preset_name,
        "mental_model_id": result.get("id") or result.get("mental_model_id"),
        "payload": payload,
    }


async def list_presets(
    *,
    engine: Any,
    bank_id: str,
    request_context: Any,
) -> list[dict[str, Any]]:
    """Return all identity presets known to a bank."""
    try:
        models = await engine.list_mental_models(
            bank_id=bank_id,
            tags=[_PRESET_TAG],
            request_context=request_context,
        )
    except Exception as exc:
        logger.warning("[presets] list failed: %s", exc)
        return []
    out: list[dict[str, Any]] = []
    items = models if isinstance(models, list) else models.get("mental_models", [])
    for entry in items:
        content = entry.get("content") if isinstance(entry, dict) else None
        try:
            payload = json.loads(content) if content else {}
        except json.JSONDecodeError:
            payload = {}
        out.append(
            {
                "mental_model_id": entry.get("id") if isinstance(entry, dict) else None,
                "preset_name": payload.get("preset_name"),
                "soul_encoding": payload.get("soul_encoding"),
                "disposition_modifiers": payload.get("disposition_modifiers"),
            }
        )
    return out


async def hydrate_preset(
    *,
    engine: Any,
    bank_id: str,
    preset_name: str,
    request_context: Any,
) -> dict[str, Any]:
    """Apply a preset's soul_encoding (and optional disposition modifiers)
    to a bank by calling encode_soul + update_bank under the hood.

    Returns the encode_soul result on success.
    """
    presets = await list_presets(engine=engine, bank_id=bank_id, request_context=request_context)
    match = next((p for p in presets if p.get("preset_name") == preset_name), None)
    if match is None:
        return {"status": "not_found", "preset_name": preset_name}

    encoding = match.get("soul_encoding") or {}
    if not encoding:
        return {"status": "invalid", "preset_name": preset_name, "error": "missing soul_encoding"}

    from entelechy_api.engine.soul import SoulEncoding
    from entelechy_api.engine.soul.operations import encode_soul

    try:
        soul_obj = SoulEncoding(**encoding)
    except Exception as exc:
        return {"status": "invalid", "preset_name": preset_name, "error": str(exc)}

    result = await encode_soul(
        engine=engine,
        bank_id=bank_id,
        encoding=soul_obj,
        sync_disposition=True,
        sync_mission=True,
        sync_directives=True,
        request_context=request_context,
    )
    return {
        "status": "hydrated",
        "preset_name": preset_name,
        "soul_result": result,
    }
