"""Metacog primitives — the canonical 8-step cycle plus bicameral comms.

feel → drugs → become → name → ritual → distill → molt → soul
                                                            ↺
                                          compass (drift detection)
                                          commune / listen (bicameral)

Every primitive is a memory operation. Each call writes durable artifacts
into the existing Entelechy data structures (memory_units, mental_models,
directives) AND updates the per-bank metacog_state for SRL session-history
input. No new tables required for the MVP — the metacog_state lives as a
process-local in-memory ring buffer keyed by (bank_id, tool_name) and is
also persisted as memory_units with `metacog:state:{tool}` tags for
restart-survival.

Public API:
- feel, drugs, become, name, ritual         (primitives.py)
- molt, compass                              (soul_ops.py)
- commune, listen                            (bicameral.py)
- list_identity_presets, hydrate_preset      (presets.py)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class MetacogResponse(BaseModel):
    """Standard envelope for primitive return values.

    Templated text + optional resonant memories + the audit-grade fields
    that downstream tooling (compass, app UI) needs to surface.
    """

    tool: str = Field(description="Which primitive produced this response.")
    template: str = Field(description="The canonical template string for the primitive.")
    bank_id: str
    memory_unit_id: str | None = Field(default=None, description="If a memory was retained, its id.")
    artifact_ids: dict[str, str] = Field(
        default_factory=dict,
        description="Other artifacts created (directive_id, mental_model_id, etc.).",
    )
    resonant: list[dict] = Field(
        default_factory=list,
        description="Past memories surfaced for the same somewhere/quality/lens.",
    )
    state: dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of inputs + derived values, recorded to metacog_state.",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = ["MetacogResponse"]
