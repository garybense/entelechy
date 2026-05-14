"""Unit tests for entelechy_api.engine.srl.synthesis with a mocked LLM."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from entelechy_api.engine.soul import SoulEncoding
from entelechy_api.engine.srl.checkpoint import CheckpointInput
from entelechy_api.engine.srl.synthesis import (
    _SynthesisOutput,
    coerce_uuid,
    synthesize_state_vector,
)


class _FakeLLM:
    """Records the most recent call args; returns a configured response."""

    def __init__(self, response):
        self.response = response
        self.last_messages = None
        self.last_kwargs = None

    async def call(self, messages, **kwargs):
        self.last_messages = messages
        self.last_kwargs = kwargs
        return self.response


def _make_checkpoint() -> CheckpointInput:
    return CheckpointInput(
        soul_id="soul-test",
        version=2,
        encoding=SoulEncoding(
            identity="researcher×operator",
            posture="skeptical | curious | precise",
            substrate="caffeinated, focused",
            aesthetics="density > verbosity",
            relations="team = primary",
            active="building srl",
            covenant="no half measures | verify before claiming",
            sigil="🜁",
        ),
        parent_id=None,
        age_seconds=120.0,
    )


@pytest.mark.asyncio
async def test_synthesis_passes_pydantic_response_format():
    llm = _FakeLLM(_SynthesisOutput(active_focus=["test"]))
    await synthesize_state_vector(
        llm_provider=llm,
        query="who am i now",
        weighted_memories=[],
        checkpoint=None,
        recent_metacog_state=[],
    )
    assert llm.last_kwargs is not None
    assert llm.last_kwargs["response_format"] is _SynthesisOutput
    assert llm.last_kwargs["scope"] == "srl.synthesis"
    # System message must mention the patent-grade phrasing
    sys_content = llm.last_messages[0]["content"]
    assert "State Vector" in sys_content
    assert "re-derived" in sys_content


@pytest.mark.asyncio
async def test_synthesis_returns_pydantic_response_unchanged():
    expected = _SynthesisOutput(
        posture_vector={"skeptical": 0.8},
        active_focus=["srl reconstruction"],
        covenant_active=["verify before claiming"],
    )
    llm = _FakeLLM(expected)
    result = await synthesize_state_vector(
        llm_provider=llm,
        query="bearing check",
        weighted_memories=[{"id": "m1", "text": "memory text", "weight": 0.7, "tags": ["t"]}],
        checkpoint=_make_checkpoint(),
        recent_metacog_state=[{"tool_name": "feel", "state_data": {"sigil": "🌫️"}}],
    )
    assert result == expected


@pytest.mark.asyncio
async def test_synthesis_normalizes_dict_response():
    llm = _FakeLLM({"posture_vector": {"open": 0.6}, "active_focus": ["x"]})
    result = await synthesize_state_vector(
        llm_provider=llm,
        query="q",
        weighted_memories=[],
        checkpoint=None,
        recent_metacog_state=[],
    )
    assert result.posture_vector == {"open": 0.6}
    assert result.active_focus == ["x"]


@pytest.mark.asyncio
async def test_synthesis_returns_empty_on_llm_failure():
    class _BoomLLM:
        async def call(self, messages, **kwargs):
            raise RuntimeError("upstream timeout")

    result = await synthesize_state_vector(
        llm_provider=_BoomLLM(),
        query="q",
        weighted_memories=[],
        checkpoint=None,
        recent_metacog_state=[],
    )
    # Cold fallback is an empty vector — reconstruction never crashes the caller.
    assert isinstance(result, _SynthesisOutput)
    assert result.posture_vector == {}
    assert result.active_focus == []


@pytest.mark.asyncio
async def test_synthesis_returns_empty_on_unexpected_type():
    llm = _FakeLLM("just a string")
    result = await synthesize_state_vector(
        llm_provider=llm,
        query="q",
        weighted_memories=[],
        checkpoint=None,
        recent_metacog_state=[],
    )
    assert result == _SynthesisOutput()


@pytest.mark.asyncio
async def test_synthesis_includes_checkpoint_in_prompt_when_present():
    llm = _FakeLLM(_SynthesisOutput())
    await synthesize_state_vector(
        llm_provider=llm,
        query="test",
        weighted_memories=[],
        checkpoint=_make_checkpoint(),
        recent_metacog_state=[],
    )
    user_content = llm.last_messages[1]["content"]
    assert "Soul checkpoint v2" in user_content
    assert "no half measures" in user_content


@pytest.mark.asyncio
async def test_synthesis_handles_no_checkpoint():
    llm = _FakeLLM(_SynthesisOutput())
    await synthesize_state_vector(
        llm_provider=llm,
        query="cold start",
        weighted_memories=[],
        checkpoint=None,
        recent_metacog_state=[],
    )
    user_content = llm.last_messages[1]["content"]
    assert "no encoded checkpoint" in user_content


def test_coerce_uuid_accepts_uuid():
    u = uuid4()
    assert coerce_uuid(u) is u


def test_coerce_uuid_accepts_string():
    assert coerce_uuid("00000000-0000-0000-0000-000000000001") is not None


def test_coerce_uuid_rejects_garbage():
    assert coerce_uuid("not-a-uuid") is None
    assert coerce_uuid(42) is None
    assert coerce_uuid(None) is None
