"""Policy history persistence + inertia against a real Postgres (set POLICY_STORE_TEST_DSN)."""
import os
import re

import asyncpg
import pytest

from entelechy_api.engine.mwpm import PolicyParams
from entelechy_api.engine.mwpm.store import list_policies, read_previous_policy, save_policy

DSN = os.environ.get("POLICY_STORE_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="POLICY_STORE_TEST_DSN not set")

MIGRATION = os.path.join(
    os.path.dirname(__file__), "..", "entelechy_api", "alembic", "versions", "m8n9o0p1q2r3_add_policy_history_table.py"
)


class _Engine:
    def __init__(self, pool):
        self._pool = pool

    async def _get_pool(self):
        return self._pool


@pytest.fixture
async def engine():
    pool = await asyncpg.create_pool(DSN)
    sql = re.search(r'CREATE TABLE IF NOT EXISTS \{schema\}policy_history \((.*?)\n        """', open(MIGRATION).read(), re.S)
    async with pool.acquire() as c:
        await c.execute("DROP TABLE IF EXISTS policy_history")
        await c.execute("CREATE TABLE policy_history (" + sql.group(1))
    yield _Engine(pool)
    await pool.close()


@pytest.mark.asyncio
async def test_roundtrip_and_latest_wins(engine):
    assert await read_previous_policy(engine, "b") is None
    first = PolicyParams(verbosity=0.2, rationale="first")
    second = PolicyParams(verbosity=0.6, rationale="second; Policy inertia epsilon-bound enforced")
    await save_policy(engine, "b", source="bootstrap", policy=first, previous=None, vector_f={"success_rate": 0.5}, state_vector=None)
    await save_policy(engine, "b", source="distill", policy=second, previous=first, vector_f=None, state_vector={"drift_signal": 0.1})
    await save_policy(engine, "other", source="bootstrap", policy=PolicyParams(verbosity=0.9), previous=None, vector_f=None, state_vector=None)

    prev = await read_previous_policy(engine, "b")
    assert prev.verbosity == 0.6
    rows = await list_policies(engine, "b")
    assert [r["source"] for r in rows] == ["distill", "bootstrap"]
    assert rows[0]["inertia_applied"] is True and rows[1]["inertia_applied"] is False
    assert rows[0]["state_vector"] == {"drift_signal": 0.1}
    assert rows[1]["vector_f"] == {"success_rate": 0.5}
    assert len(await list_policies(engine, "b", limit=1)) == 1
