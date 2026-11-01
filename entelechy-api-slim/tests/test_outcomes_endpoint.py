"""POST /v1/default/banks/{bank_id}/outcomes retains a tagged memory (engine stubbed, no database)."""
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from entelechy_api.api import create_app
from entelechy_api.engine.mwpm.frequency import OUTCOME_FAILURE_TAG, OUTCOME_SUCCESS_TAG


@pytest.fixture
def memory():
    m = MagicMock()
    m.submit_async_retain = AsyncMock(return_value={"operation_id": "op-1", "items_count": 1})
    return m


@pytest.fixture
async def client(memory):
    app = create_app(memory, initialize_memory=False)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        yield c


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome,tag", [("success", OUTCOME_SUCCESS_TAG), ("failure", OUTCOME_FAILURE_TAG)])
async def test_outcome_is_retained_with_tag(client, memory, outcome, tag):
    r = await client.post(
        "/v1/default/banks/b1/outcomes",
        json={"outcome": outcome, "session_id": "s1", "score": 0.7, "policy": {"verbosity": 0.4}, "note": "answered"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["operation_id"] == "op-1"
    args, kwargs = memory.submit_async_retain.call_args
    assert args[0] == "b1"
    item = args[1][0]
    assert item["tags"] == [tag]
    assert item["document_id"] == "outcome-s1"
    assert f"Outcome: {outcome}." in item["content"] and "Score: 0.7." in item["content"]
    assert "answered" in item["content"] and '"verbosity": 0.4' in item["content"]


@pytest.mark.asyncio
async def test_invalid_outcome_rejected(client, memory):
    r = await client.post("/v1/default/banks/b1/outcomes", json={"outcome": "maybe"})
    assert r.status_code == 422
    memory.submit_async_retain.assert_not_called()
