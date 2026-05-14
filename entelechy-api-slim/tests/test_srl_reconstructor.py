"""Integration tests for entelechy_api.engine.srl.reconstructor with mock engine."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from entelechy_api.engine.soul import SoulEncoding
from entelechy_api.engine.srl import StateVector
from entelechy_api.engine.srl.reconstructor import (
    _compute_drift,
    _extract_memory_dicts,
    _memory_age_seconds,
    _normalize_tokens,
    reconstruct_state,
)
from entelechy_api.engine.srl.synthesis import _SynthesisOutput


class _StubLLM:
    def __init__(self, response: _SynthesisOutput):
        self.response = response

    async def call(self, messages, **kwargs):
        return self.response


def _build_engine(*, recall_payload, soul_payload, llm_response):
    """Construct a minimal engine duck-type sufficient for reconstruct_state."""
    engine = SimpleNamespace()
    engine._reflect_llm_config = _StubLLM(llm_response)
    engine._llm_config = engine._reflect_llm_config

    async def _recall(**kwargs):
        if recall_payload is None:
            raise RuntimeError("recall offline")

        class _Result:
            def model_dump(self_inner):
                return recall_payload

        return _Result()

    engine.recall_async = _recall

    async def _authenticate_tenant(rc):
        return "default"

    engine._authenticate_tenant = _authenticate_tenant

    async def _get_active_soul(**kwargs):
        return soul_payload

    # The checkpoint reader imports get_active_soul directly; patch via attr
    # is unnecessary because read_checkpoint uses the module-level import.
    # Instead, monkey-patching is done in the test that needs it.
    engine._stub_soul = soul_payload
    return engine


@pytest.mark.asyncio
async def test_reconstruct_state_full_pipeline(monkeypatch):
    soul_payload = {
        "soul_id": "soul-1",
        "version": 1,
        "parent_id": None,
        "encoding": {
            "identity": "researcher",
            "posture": "skeptical | precise",
            "substrate": "focused",
            "aesthetics": "density > verbosity",
            "relations": "team",
            "active": "build srl",
            "covenant": "verify | no half measures",
            "sigil": "🜁",
        },
        "created_at": datetime.now(timezone.utc) - timedelta(seconds=60),
    }

    async def _stub_get_active_soul(**kwargs):
        return soul_payload

    monkeypatch.setattr(
        "entelechy_api.engine.srl.checkpoint.get_active_soul",
        _stub_get_active_soul,
    )

    recall_payload = {
        "memories": [
            {
                "id": str(uuid4()),
                "text": "felt sense: clarity expanding",
                "tags": ["metacog:felt-sense"],
                "score": 0.9,
                "event_date": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
            },
            {
                "id": str(uuid4()),
                "text": "decided to verify before claiming",
                "tags": ["metacog:naming"],
                "score": 0.7,
                "event_date": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
            },
        ]
    }

    llm_response = _SynthesisOutput(
        posture_vector={"skeptical": 0.8, "precise": 0.6},
        aesthetic_vector={"density": 0.9},
        covenant_active=["verify before claiming", "no half measures"],
        active_focus=["srl reconstruction"],
        affect_signature={"clarity": 0.6},
        persona_lens=None,
        transient_modifiers={},
    )

    engine = _build_engine(
        recall_payload=recall_payload,
        soul_payload=soul_payload,
        llm_response=llm_response,
    )

    state = await reconstruct_state(
        engine=engine,
        bank_id="test_bank",
        query="who am i right now",
        request_context=SimpleNamespace(api_key=None),
    )

    assert isinstance(state, StateVector)
    assert state.posture_vector == {"skeptical": 0.8, "precise": 0.6}
    assert state.covenant_active == ["verify before claiming", "no half measures"]
    assert state.active_focus == ["srl reconstruction"]
    assert state.reconstruction_id  # uuid populated
    assert len(state.source_memory_ids) == 2
    assert state.decay_profile["name"] == "half_life"
    # checkpoint covenant matches reconstructed covenant fully → drift near 0
    assert state.drift_signal < 0.5


@pytest.mark.asyncio
async def test_reconstruct_state_handles_recall_failure(monkeypatch):
    async def _stub_get_active_soul(**kwargs):
        return None

    monkeypatch.setattr(
        "entelechy_api.engine.srl.checkpoint.get_active_soul",
        _stub_get_active_soul,
    )

    engine = _build_engine(
        recall_payload=None,  # triggers RuntimeError in mock recall
        soul_payload=None,
        llm_response=_SynthesisOutput(),
    )

    state = await reconstruct_state(
        engine=engine,
        bank_id="cold_bank",
        query="anything",
        request_context=SimpleNamespace(api_key=None),
    )

    # Pipeline is robust: empty vector with provenance still populated.
    assert isinstance(state, StateVector)
    assert state.source_memory_ids == []
    assert state.drift_signal == 0.0
    assert state.reconstruction_id


@pytest.mark.asyncio
async def test_reconstruct_state_caches_with_key(monkeypatch):
    async def _stub_get_active_soul(**kwargs):
        return None

    monkeypatch.setattr(
        "entelechy_api.engine.srl.checkpoint.get_active_soul",
        _stub_get_active_soul,
    )

    call_count = 0

    class _CountingLLM:
        async def call(self_inner, messages, **kwargs):
            nonlocal call_count
            call_count += 1
            return _SynthesisOutput(active_focus=[f"call-{call_count}"])

    engine = SimpleNamespace()
    engine._reflect_llm_config = _CountingLLM()
    engine._llm_config = engine._reflect_llm_config

    async def _recall(**kwargs):
        class _R:
            def model_dump(self_inner):
                return {"memories": []}

        return _R()

    engine.recall_async = _recall

    state1 = await reconstruct_state(
        engine=engine,
        bank_id="cache_bank",
        query="q",
        request_context=SimpleNamespace(api_key=None),
        cache_key="op-1",
    )
    state2 = await reconstruct_state(
        engine=engine,
        bank_id="cache_bank",
        query="q",
        request_context=SimpleNamespace(api_key=None),
        cache_key="op-1",
    )

    # Same reconstruction_id proves cache hit
    assert state1.reconstruction_id == state2.reconstruction_id
    assert call_count == 1


def test_extract_memory_dicts_handles_flat_list():
    payload = {"memories": [{"id": "a"}, {"id": "b"}]}
    out = _extract_memory_dicts(SimpleNamespace(model_dump=lambda: payload))
    assert [m["id"] for m in out] == ["a", "b"]


def test_extract_memory_dicts_handles_nested_buckets():
    payload = {
        "world": {"results": [{"id": "w1"}]},
        "experience": {"memories": [{"id": "e1"}]},
    }
    out = _extract_memory_dicts(SimpleNamespace(model_dump=lambda: payload))
    ids = sorted(m["id"] for m in out)
    assert ids == ["e1", "w1"]


def test_extract_memory_dicts_handles_none():
    assert _extract_memory_dicts(None) == []


def test_memory_age_seconds_uses_event_date_first():
    now_epoch = datetime.now(timezone.utc).timestamp()
    mem = {
        "event_date": datetime.now(timezone.utc) - timedelta(seconds=300),
        "created_at": datetime.now(timezone.utc) - timedelta(seconds=100),
    }
    age = _memory_age_seconds(mem, now_epoch)
    assert 290 < age < 310


def test_memory_age_seconds_falls_back_when_missing():
    assert _memory_age_seconds({}, datetime.now(timezone.utc).timestamp()) == 0.0


def test_compute_drift_no_checkpoint_is_zero():
    synth = _SynthesisOutput(covenant_active=["x"])
    assert _compute_drift(synth, None) == 0.0


def test_compute_drift_full_alignment_is_low():
    from entelechy_api.engine.srl.checkpoint import CheckpointInput

    cp = CheckpointInput(
        soul_id="x",
        version=1,
        encoding=SoulEncoding(
            identity="i",
            posture="p",
            substrate="s",
            aesthetics="a",
            relations="r",
            active="act",
            covenant="verify before claiming",
            sigil="🜁",
        ),
        parent_id=None,
        age_seconds=0.0,
    )
    synth = _SynthesisOutput(covenant_active=["verify before claiming"])
    assert _compute_drift(synth, cp) < 0.1


def test_compute_drift_total_disjoint_is_high():
    from entelechy_api.engine.srl.checkpoint import CheckpointInput

    cp = CheckpointInput(
        soul_id="x",
        version=1,
        encoding=SoulEncoding(
            identity="i",
            posture="p",
            substrate="s",
            aesthetics="a",
            relations="r",
            active="act",
            covenant="verify always",
            sigil="🜁",
        ),
        parent_id=None,
        age_seconds=0.0,
    )
    synth = _SynthesisOutput(covenant_active=["completely different commitment"])
    assert _compute_drift(synth, cp) > 0.5


def test_normalize_tokens_filters_short_words():
    assert "verify" in _normalize_tokens("Verify before claiming")
    assert "to" not in _normalize_tokens("to be or not")
