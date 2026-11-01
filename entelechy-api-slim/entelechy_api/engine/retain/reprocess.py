"""Rebuild memories from the source text stored with each document.

Memory units hold embeddings, so they have to be rebuilt when the embedding model
changes. The documents table keeps the original text plus the retain parameters
(context, event date, metadata, tags), which is enough to run extraction again.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from ..db_utils import acquire_with_retry
from ..schema import fq_table

logger = logging.getLogger(__name__)


def _content_item(row: Any) -> dict[str, Any]:
    params = row["retain_params"]
    if isinstance(params, str):
        params = json.loads(params)
    params = params or {}
    item: dict[str, Any] = {"content": row["original_text"], "document_id": row["id"]}
    if params.get("context"):
        item["context"] = params["context"]
    if params.get("metadata"):
        item["metadata"] = params["metadata"]
    if params.get("event_date"):
        item["event_date"] = datetime.fromisoformat(params["event_date"])
    if row["tags"]:
        item["tags"] = list(row["tags"])
    return item


async def reprocess_documents(
    engine: Any, bank_id: str, request_context: Any, *, batch_size: int = 25
) -> dict[str, Any]:
    """Queue a retain for every document of the bank that has no memory units.

    Documents that already have memories are skipped, so calling this twice does not
    duplicate work. Stored chunks are cleared for the documents being rebuilt: retain
    otherwise treats an unchanged document with chunks as already extracted.
    """
    pool = await engine._get_pool()
    async with acquire_with_retry(pool) as conn:
        rows = await conn.fetch(
            f"""
            SELECT d.id, d.original_text, d.retain_params, d.tags
            FROM {fq_table('documents')} d
            WHERE d.bank_id = $1
              AND d.original_text IS NOT NULL AND d.original_text <> ''
              AND NOT EXISTS (
                  SELECT 1 FROM {fq_table('memory_units')} m
                  WHERE m.bank_id = d.bank_id AND m.document_id = d.id
              )
            ORDER BY d.created_at
            """,
            bank_id,
        )
        total = await conn.fetchval(f"SELECT COUNT(*) FROM {fq_table('documents')} WHERE bank_id = $1", bank_id)
        ids = [r["id"] for r in rows]
        if ids:
            await conn.execute(
                f"DELETE FROM {fq_table('chunks')} WHERE bank_id = $1 AND document_id = ANY($2::text[])",
                bank_id,
                ids,
            )

    operations = []
    for i in range(0, len(rows), batch_size):
        items = [_content_item(r) for r in rows[i : i + batch_size]]
        result = await engine.submit_async_retain(bank_id, items, request_context=request_context)
        operations.append(result)
    logger.info(f"Reprocess bank={bank_id}: {len(rows)} of {total} documents queued in {len(operations)} operations")
    return {
        "bank_id": bank_id,
        "documents_total": total,
        "documents_queued": len(rows),
        "documents_skipped": total - len(rows),
        "operations": operations,
    }
