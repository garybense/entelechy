"""Persistence for computed policies.

Every bootstrap and distill stores the policy it produced. The most recent one is
P_{t-1}, which `modulate_policy` clamps the next policy against (policy inertia).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..db_utils import acquire_with_retry
from ..schema import fq_table
from . import PolicyParams

logger = logging.getLogger(__name__)

_POLICY_FIELDS = ("verbosity", "abstraction", "creativity", "empathy", "rigor", "tool_use_probability")


def policy_to_dict(policy: PolicyParams) -> dict[str, float]:
    return {name: getattr(policy, name) for name in _POLICY_FIELDS}


async def read_previous_policy(engine: Any, bank_id: str) -> PolicyParams | None:
    """Latest stored policy for the bank, or None when none exists yet."""
    try:
        pool = await engine._get_pool()
        async with acquire_with_retry(pool) as conn:
            row = await conn.fetchrow(
                f"SELECT policy FROM {fq_table('policy_history')} WHERE bank_id = $1 ORDER BY created_at DESC LIMIT 1",
                bank_id,
            )
    except Exception as exc:
        logger.warning("Policy history read failed for bank %s, no inertia applied: %s", bank_id, exc)
        return None
    if row is None:
        return None
    raw = row["policy"]
    data = json.loads(raw) if isinstance(raw, str) else raw
    return PolicyParams(**{k: data[k] for k in _POLICY_FIELDS if k in data})


async def save_policy(
    engine: Any,
    bank_id: str,
    *,
    source: str,
    policy: PolicyParams,
    previous: PolicyParams | None,
    vector_f: dict[str, Any] | None,
    state_vector: dict[str, Any] | None,
) -> None:
    """Store a computed policy. Failures are logged: the response must not depend on history."""
    try:
        pool = await engine._get_pool()
        async with acquire_with_retry(pool) as conn:
            await conn.execute(
                f"""
                INSERT INTO {fq_table('policy_history')}
                    (bank_id, source, policy, rationale, vector_f, state_vector, inertia_applied)
                VALUES ($1, $2, $3::jsonb, $4, $5::jsonb, $6::jsonb, $7)
                """,
                bank_id,
                source,
                json.dumps(policy_to_dict(policy)),
                policy.rationale,
                json.dumps(vector_f, default=str) if vector_f is not None else None,
                json.dumps(state_vector, default=str) if state_vector is not None else None,
                previous is not None and "inertia" in (policy.rationale or "").lower(),
            )
    except Exception as exc:
        logger.warning("Policy history write failed for bank %s: %s", bank_id, exc)


async def list_policies(engine: Any, bank_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Stored policies for the bank, newest first."""
    pool = await engine._get_pool()
    async with acquire_with_retry(pool) as conn:
        rows = await conn.fetch(
            f"""
            SELECT id, source, created_at, policy, rationale, vector_f, state_vector, inertia_applied
            FROM {fq_table('policy_history')}
            WHERE bank_id = $1 ORDER BY created_at DESC LIMIT $2
            """,
            bank_id,
            limit,
        )

    def _j(v: Any) -> Any:
        return json.loads(v) if isinstance(v, str) else v

    return [
        {
            "id": str(r["id"]),
            "source": r["source"],
            "created_at": r["created_at"].isoformat(),
            "policy": _j(r["policy"]),
            "rationale": r["rationale"],
            "vector_f": _j(r["vector_f"]),
            "state_vector": _j(r["state_vector"]),
            "inertia_applied": r["inertia_applied"],
        }
        for r in rows
    ]
