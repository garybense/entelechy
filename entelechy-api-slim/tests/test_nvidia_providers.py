import asyncio
import json

import httpx

from entelechy_api.engine.cross_encoder import NvidiaCrossEncoder
from entelechy_api.engine.embeddings import NvidiaEmbeddings
from entelechy_api.engine.retain.embedding_utils import generate_query_embeddings_batch


def test_embeddings_passage_query_and_dimensions():
    seen = []

    def handler(req: httpx.Request):
        body = json.loads(req.content)
        seen.append(body)
        data = [{"index": i, "embedding": [float(i)] * 4} for i in reversed(range(len(body["input"])))]
        return httpx.Response(200, json={"data": data})

    emb = NvidiaEmbeddings("k", "m", "http://x/v1", dimensions=4, batch_size=2, transport=httpx.MockTransport(handler))
    asyncio.run(emb.initialize())
    assert emb.dimension == 4
    out = emb.encode(["a", "b", "c"])
    assert [v[0] for v in out] == [0.0, 1.0, 0.0]  # order restored per batch
    assert seen[-1]["input_type"] == "passage" and seen[-1]["dimensions"] == 4
    asyncio.run(generate_query_embeddings_batch(emb, ["q"]))
    assert seen[-1]["input_type"] == "query"


def test_reranker_maps_rankings_to_pairs():
    def handler(req: httpx.Request):
        body = json.loads(req.content)
        assert body["query"] == {"text": "q"}
        n = len(body["passages"])
        return httpx.Response(200, json={"rankings": [{"index": i, "logit": float(i) * -1} for i in range(n)][::-1]})

    ce = NvidiaCrossEncoder("k", "m", "http://x/rerank", transport=httpx.MockTransport(handler))

    async def run():
        await ce.initialize()
        return await ce.predict([("q", "a"), ("q", "b"), ("q", "c")])

    assert asyncio.run(run()) == [0.0, -1.0, -2.0]
