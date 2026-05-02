"""Soul encoding operations for the memory engine.

Provides the core soul CRUD operations as standalone async functions
that operate on the existing mental_models table. These are called by
the MCP tool registrations and by the engine's public interface.

Soul encodings are stored as mental models with:
- subtype = 'soul'
- structured_content = soul schema JSONB
- content = human-readable rendering
- soul_version = lineage counter
- soul_parent_id = molt ancestry

The active soul is the highest-versioned soul encoding for a bank.
"""

import json
import logging
import uuid
from typing import Any

from entelechy_api.engine.soul import (
    SoulEncoding,
    SoulResponse,
    covenant_to_directives,
    soul_to_content,
    soul_to_disposition,
    soul_to_mission,
    soul_to_structured,
    structured_to_soul,
)

logger = logging.getLogger(__name__)


async def encode_soul(
    engine: Any,
    bank_id: str,
    encoding: SoulEncoding,
    *,
    sync_disposition: bool = True,
    sync_mission: bool = True,
    sync_directives: bool = True,
    request_context: Any,
) -> dict[str, Any]:
    """Encode a new soul version for a bank.

    This is the central soul operation. It:
    1. Creates a new mental model with subtype='soul'
    2. Increments the soul version
    3. Optionally syncs disposition, mission, and directives

    Args:
        engine: MemoryEngine instance
        bank_id: Target bank
        encoding: The soul encoding to persist
        sync_disposition: Update bank disposition from soul
        sync_mission: Update bank retain_mission from soul
        sync_directives: Create directives from covenant
        request_context: Auth context

    Returns:
        Dict with soul_id, version, encoding, sync results
    """
    from entelechy_api.engine.memory_engine import acquire_with_retry, fq_table

    await engine._authenticate_tenant(request_context)
    backend = await engine._get_backend()

    # Determine next version by finding the current highest
    async with acquire_with_retry(backend) as conn:
        current_max = await conn.fetchval(
            f"SELECT COALESCE(MAX(soul_version), 0) FROM {fq_table('mental_models')} "
            f"WHERE bank_id = $1 AND subtype = 'soul'",
            bank_id,
        )
        next_version = (current_max or 0) + 1

        # Find current active soul ID for parent linkage
        current_soul_id = await conn.fetchval(
            f"SELECT id FROM {fq_table('mental_models')} "
            f"WHERE bank_id = $1 AND subtype = 'soul' "
            f"ORDER BY soul_version DESC LIMIT 1",
            bank_id,
        )

    # Create the soul as a mental model
    soul_id = f"soul-{uuid.uuid4().hex[:12]}"
    content = soul_to_content(encoding)
    structured = soul_to_structured(encoding)

    # Use the engine's create_mental_model but we need to set subtype and soul fields
    # directly via SQL since create_mental_model always sets subtype='pinned'
    from entelechy_api.engine.retain import embedding_utils

    embedding_text = f"soul encoding {encoding.identity} {encoding.posture}"
    try:
        embeddings = await embedding_utils.generate_embeddings_batch(
            engine.embeddings, [embedding_text]
        )
        embedding_str = str(embeddings[0]) if embeddings else None
    except Exception as e:
        logger.warning(f"[SOUL] Embedding generation failed (non-fatal): {e}")
        embedding_str = None

    async with acquire_with_retry(backend) as conn:
        row = await conn.fetchrow(
            f"""
            INSERT INTO {fq_table("mental_models")}
            (id, bank_id, subtype, name, description, source_query, content,
             embedding, tags, max_tokens, soul_version, soul_parent_id,
             structured_content)
            VALUES ($1, $2, 'soul', $3, $4, $5, $6, $7, $8, 2048, $9, $10, $11)
            RETURNING id, bank_id, name, content, tags, soul_version,
                      soul_parent_id, created_at, structured_content
            """,
            soul_id,
            bank_id,
            f"Soul v{next_version}",
            f"Soul encoding version {next_version} for bank {bank_id}",
            "Who is this agent and what has it committed to?",
            content,
            embedding_str,
            ["soul", "identity"],
            next_version,
            current_soul_id,
            json.dumps(structured),
        )

    logger.info(
        f"[SOUL] Encoded soul v{next_version} for bank {bank_id} "
        f"(id={soul_id}, parent={current_soul_id})"
    )

    # Sync operations
    sync_results = {}

    if sync_disposition:
        disposition = soul_to_disposition(encoding)
        try:
            await engine.update_bank_disposition(
                bank_id=bank_id,
                disposition=disposition,
                request_context=request_context,
            )
            sync_results["disposition"] = disposition
            logger.info(f"[SOUL] Synced disposition for bank {bank_id}: {disposition}")
        except Exception as e:
            logger.warning(f"[SOUL] Failed to sync disposition: {e}")
            sync_results["disposition_error"] = str(e)

    if sync_mission:
        mission = soul_to_mission(encoding)
        try:
            await engine.update_bank(
                bank_id=bank_id,
                mission=mission,
                request_context=request_context,
            )
            sync_results["mission"] = mission
            logger.info(f"[SOUL] Synced mission for bank {bank_id}")
        except Exception as e:
            logger.warning(f"[SOUL] Failed to sync mission: {e}")
            sync_results["mission_error"] = str(e)

    if sync_directives:
        directive_specs = covenant_to_directives(encoding)
        created_directives = []
        for spec in directive_specs:
            try:
                directive = await engine.create_directive(
                    bank_id=bank_id,
                    name=spec["name"],
                    content=spec["content"],
                    priority=10,  # Soul covenant directives are high priority
                    tags=["soul-covenant", f"soul-v{next_version}"],
                    request_context=request_context,
                )
                created_directives.append(directive.get("id") or directive.get("name"))
            except Exception as e:
                logger.warning(f"[SOUL] Failed to create directive '{spec['name']}': {e}")
        sync_results["directives_created"] = len(created_directives)
        logger.info(
            f"[SOUL] Created {len(created_directives)} covenant directives "
            f"for bank {bank_id}"
        )

    return {
        "soul_id": soul_id,
        "bank_id": bank_id,
        "version": next_version,
        "parent_id": current_soul_id,
        "encoding": encoding.model_dump(),
        "sync": sync_results,
        "status": "encoded",
        "message": f"Soul v{next_version} encoded. "
        + (f"Disposition, mission, and {sync_results.get('directives_created', 0)} "
           f"covenant directives synced." if sync_disposition else ""),
    }


async def get_active_soul(
    engine: Any,
    bank_id: str,
    *,
    request_context: Any,
) -> dict[str, Any] | None:
    """Get the current active soul encoding for a bank.

    The active soul is the highest-versioned soul in the mental_models table.

    Returns:
        Soul dict with encoding, version, lineage info, or None if no soul exists.
    """
    from entelechy_api.engine.memory_engine import acquire_with_retry, fq_table

    await engine._authenticate_tenant(request_context)
    backend = await engine._get_backend()

    async with acquire_with_retry(backend) as conn:
        row = await conn.fetchrow(
            f"""
            SELECT id, bank_id, name, content, structured_content,
                   soul_version, soul_parent_id, tags, created_at
            FROM {fq_table("mental_models")}
            WHERE bank_id = $1 AND subtype = 'soul'
            ORDER BY soul_version DESC
            LIMIT 1
            """,
            bank_id,
        )

    if not row:
        return None

    structured = row["structured_content"]
    if isinstance(structured, str):
        try:
            structured = json.loads(structured)
        except json.JSONDecodeError:
            structured = None

    encoding = structured_to_soul(structured) if structured else None

    return {
        "soul_id": row["id"],
        "bank_id": row["bank_id"],
        "version": row["soul_version"],
        "parent_id": row["soul_parent_id"],
        "encoding": encoding.model_dump() if encoding else None,
        "content": row["content"],
        "tags": row["tags"] or [],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


async def list_soul_lineage(
    engine: Any,
    bank_id: str,
    *,
    limit: int = 50,
    request_context: Any,
) -> list[dict[str, Any]]:
    """List all soul versions for a bank in reverse chronological order.

    This is the molt lineage — each entry shows who the agent was at that point,
    with parent links showing the evolution chain.

    Returns:
        List of soul dicts with version, encoding summary, timestamps.
    """
    from entelechy_api.engine.memory_engine import acquire_with_retry, fq_table

    await engine._authenticate_tenant(request_context)
    backend = await engine._get_backend()

    async with acquire_with_retry(backend) as conn:
        rows = await conn.fetch(
            f"""
            SELECT id, bank_id, name, content, structured_content,
                   soul_version, soul_parent_id, tags, created_at
            FROM {fq_table("mental_models")}
            WHERE bank_id = $1 AND subtype = 'soul'
            ORDER BY soul_version DESC
            LIMIT $2
            """,
            bank_id,
            limit,
        )

    results = []
    for row in rows:
        structured = row["structured_content"]
        if isinstance(structured, str):
            try:
                structured = json.loads(structured)
            except json.JSONDecodeError:
                structured = None

        encoding = structured_to_soul(structured) if structured else None

        results.append({
            "soul_id": row["id"],
            "bank_id": row["bank_id"],
            "version": row["soul_version"],
            "parent_id": row["soul_parent_id"],
            "identity": encoding.identity if encoding else None,
            "sigil": encoding.sigil if encoding else None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })

    return results
