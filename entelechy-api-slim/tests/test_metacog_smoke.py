"""Smoke tests for entelechy_api.engine.metacog.* primitives.

These verify each primitive shapes its return envelope correctly and
records to metacog_state, using a stub engine. Deeper integration tests
against a live database are out of scope for this fast pass.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from entelechy_api.engine.metacog import MetacogResponse
from entelechy_api.engine.metacog.bicameral import (
    channel_bank_id,
    commune,
    listen,
)
from entelechy_api.engine.metacog.primitives import (
    become,
    drugs,
    feel,
    name_,
    ritual,
)
from entelechy_api.engine.metacog.state import (
    clear_state,
    get_recent_state,
    record_state,
)


def _stub_engine():
    """Minimal engine duck for primitives. retain_async returns a fixed id;
    create_directive / create_mental_model return canned ids; recall_async
    returns an empty result."""
    engine = SimpleNamespace()

    async def _retain(*, bank_id, content, context, request_context):
        return [f"mem-{abs(hash(content)) % 10**8:08d}"]

    async def _create_directive(**kwargs):
        return {"id": f"dir-{abs(hash(kwargs.get('name', ''))) % 10**6:06d}"}

    async def _create_mental_model(**kwargs):
        return {"id": f"mm-{abs(hash(kwargs.get('name', ''))) % 10**6:06d}"}

    async def _recall(**kwargs):
        return SimpleNamespace(model_dump=lambda: {"memories": []})

    async def _create_bank(**kwargs):
        return {"bank_id": kwargs.get("bank_id")}

    async def _list_mental_models(**kwargs):
        return []

    engine.retain_async = _retain
    engine.create_directive = _create_directive
    engine.create_mental_model = _create_mental_model
    engine.recall_async = _recall
    engine.create_bank = _create_bank
    engine.list_mental_models = _list_mental_models
    return engine


@pytest.fixture(autouse=True)
def _clean_state():
    asyncio.get_event_loop_policy()  # ensure module-level state available
    yield


@pytest.mark.asyncio
async def test_feel_returns_envelope_and_records_state():
    engine = _stub_engine()
    bank_id = "smoke-feel"
    await clear_state(bank_id)
    resp = await feel(
        engine=engine,
        bank_id=bank_id,
        somewhere="between the temples",
        quality="low hum, expanding",
        request_context=SimpleNamespace(),
    )
    assert isinstance(resp, MetacogResponse)
    assert resp.tool == "feel"
    assert "between the temples" in resp.template
    assert resp.memory_unit_id is not None
    history = await get_recent_state(bank_id, tool_names=["feel"])
    assert len(history) == 1
    assert history[0]["state_data"]["somewhere"] == "between the temples"


@pytest.mark.asyncio
async def test_drugs_creates_transient_directive():
    engine = _stub_engine()
    bank_id = "smoke-drugs"
    await clear_state(bank_id)
    resp = await drugs(
        engine=engine,
        bank_id=bank_id,
        substance="caffeine",
        method="oral",
        request_context=SimpleNamespace(),
    )
    assert resp.tool == "drugs"
    assert "caffeine" in resp.template
    assert "directive_id" in resp.artifact_ids


@pytest.mark.asyncio
async def test_become_creates_persona_mental_model():
    engine = _stub_engine()
    bank_id = "smoke-become"
    await clear_state(bank_id)
    resp = await become(
        engine=engine,
        bank_id=bank_id,
        name="researcher",
        lens="rigor",
        environment="lab",
        request_context=SimpleNamespace(),
    )
    assert resp.tool == "become"
    assert "researcher" in resp.template
    assert "mental_model_id" in resp.artifact_ids


@pytest.mark.asyncio
async def test_name_creates_directive_and_mental_model():
    engine = _stub_engine()
    bank_id = "smoke-name"
    await clear_state(bank_id)
    resp = await name_(
        engine=engine,
        bank_id=bank_id,
        unnamed="recurring loop",
        named="The Infinite Loop",
        power="trigger skepticism modifiers when this pattern recurs",
        request_context=SimpleNamespace(),
    )
    assert resp.tool == "name"
    assert "The Infinite Loop" in resp.template
    assert "directive_id" in resp.artifact_ids
    assert "mental_model_id" in resp.artifact_ids


@pytest.mark.asyncio
async def test_ritual_records_each_step_and_creates_immutable_model():
    engine = _stub_engine()
    bank_id = "smoke-ritual"
    await clear_state(bank_id)
    resp = await ritual(
        engine=engine,
        bank_id=bank_id,
        threshold="ship phase d",
        steps=["write code", "pass tests", "merge"],
        result="phase d shipped",
        request_context=SimpleNamespace(),
    )
    assert resp.tool == "ritual"
    assert "ship phase d" in resp.template
    # Ritual records 3 steps + 1 mental_model + the ritual_id artifact
    assert "mental_model_id" in resp.artifact_ids
    assert "ritual_id" in resp.artifact_ids
    history = await get_recent_state(bank_id, tool_names=["ritual"])
    assert history[0]["state_data"]["threshold"] == "ship phase d"


@pytest.mark.asyncio
async def test_state_history_capped_at_50():
    bank_id = "smoke-cap"
    await clear_state(bank_id)
    for i in range(60):
        await record_state(bank_id=bank_id, tool_name="feel", state_data={"i": i})
    # Buffer caps at 50, but the default get_recent_state limit is 30.
    history = await get_recent_state(bank_id, tool_names=["feel"], limit=100)
    assert len(history) == 50


@pytest.mark.asyncio
async def test_channel_bank_id_canonical():
    assert channel_bank_id("alpha-beta") == "channel:alpha-beta"
    assert channel_bank_id("channel:already") == "channel:already"


@pytest.mark.asyncio
async def test_commune_writes_to_channel_bank_and_returns_message_id():
    engine = _stub_engine()
    await clear_state("agent-a")
    out = await commune(
        engine=engine,
        channel="alpha-beta",
        from_bank="agent-a",
        to_bank="agent-b",
        thought="bearing check requested",
        request_context=SimpleNamespace(),
    )
    assert out["status"] == "sent"
    assert out["channel_bank_id"] == "channel:alpha-beta"
    assert out["message_id"] is not None


@pytest.mark.asyncio
async def test_commune_rejects_payload_failing_schema():
    engine = _stub_engine()
    out = await commune(
        engine=engine,
        channel="alpha-beta",
        from_bank="agent-a",
        to_bank="agent-b",
        thought="not json",
        request_context=SimpleNamespace(),
        schema={"required": ["topic"]},
    )
    assert out["status"] == "rejected"


@pytest.mark.asyncio
async def test_listen_returns_envelope():
    engine = _stub_engine()
    out = await listen(
        engine=engine,
        channel="alpha-beta",
        self_bank="agent-b",
        request_context=SimpleNamespace(),
    )
    assert out["status"] == "received"
    assert out["channel_bank_id"] == "channel:alpha-beta"
    assert out["messages"] == []
