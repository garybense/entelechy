import asyncio

import pytest

from entelechy_api.engine.providers.openai_compatible_llm import OpenAICompatibleLLM


def _llm(key):
    return OpenAICompatibleLLM(provider="openai", api_key=key, base_url="http://localhost:1/v1", model="m")


def test_single_key_uses_one_client():
    llm = _llm("k1")
    assert len(llm._clients) == 1
    assert llm._client is llm._client


def test_comma_separated_keys_rotate_and_batch_uses_first():
    llm = _llm("k1, k2 ,k3")
    assert llm.api_key == "k1"
    assert [c.api_key for c in llm._clients] == ["k1", "k2", "k3"]
    seen = [llm._client.api_key for _ in range(6)]
    assert seen == ["k1", "k2", "k3", "k1", "k2", "k3"]


def test_cleanup_closes_all_clients():
    llm = _llm("k1,k2")
    asyncio.run(llm.cleanup())
