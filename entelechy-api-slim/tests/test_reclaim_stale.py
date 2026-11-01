import os
import uuid

import asyncpg
import pytest

from entelechy_api.worker.poller import WorkerPoller

DSN = os.getenv("POLICY_STORE_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="POLICY_STORE_TEST_DSN not set")


class _Backend:
    def __init__(self, conn):
        self.conn = conn

    def acquire(self):
        conn = self.conn

        class _Ctx:
            async def __aenter__(self):
                return conn

            async def __aexit__(self, *a):
                return False

        return _Ctx()


async def test_reclaims_only_old_claims_from_other_workers(monkeypatch):
    conn = await asyncpg.connect(DSN)
    try:
        await conn.execute(
            """CREATE TEMP TABLE async_operations (operation_id uuid, status text, worker_id text,
               claimed_at timestamptz, updated_at timestamptz, completed_at timestamptz, error_message text,
               task_payload jsonb, result_metadata jsonb DEFAULT '{}')"""
        )
        rows = {
            "old_with_payload": ("old-host", "2 hours", "{}"),
            "old_no_payload": ("old-host", "2 hours", None),
            "recent": ("old-host", "1 minute", "{}"),
            "mine": ("me", "2 hours", "{}"),
        }
        ids = {}
        for name, (w, age, payload) in rows.items():
            ids[name] = uuid.uuid4()
            await conn.execute(
                f"INSERT INTO async_operations (operation_id,status,worker_id,claimed_at,task_payload) "
                f"VALUES ($1,'processing',$2, now() - interval '{age}', $3::jsonb)",
                ids[name], w, payload,
            )
        monkeypatch.setattr("entelechy_api.worker.poller.fq_table", lambda t, s=None: t)
        p = WorkerPoller.__new__(WorkerPoller)
        p._backend = _Backend(conn)
        p._worker_id = "me"

        async def schemas():
            return [None]

        p._get_schemas = schemas
        assert await p.reclaim_stale_tasks() == 2
        st = {n: await conn.fetchval("SELECT status FROM async_operations WHERE operation_id=$1", i) for n, i in ids.items()}
        assert st == {"old_with_payload": "pending", "old_no_payload": "failed", "recent": "processing", "mine": "processing"}
    finally:
        await conn.close()
