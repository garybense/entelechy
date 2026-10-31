"""Multi-user extension: auth, bank ownership (REST + validator), admin API.

Needs a Postgres reachable at MULTIUSER_TEST_DSN (plain Postgres is enough).
"""

import os
import uuid

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

DSN = os.environ.get("MULTIUSER_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="MULTIUSER_TEST_DSN not set")
ADMIN = "admin-key-for-tests"


@pytest_asyncio.fixture
async def env():
    from entelechy_api.extensions.builtin import multiuser as mu
    from entelechy_api.models import RequestContext

    schema = "mu_" + uuid.uuid4().hex[:8]
    store = mu.UserStore(DSN, schema, ADMIN)
    await store.start()
    mu._store = store

    app = FastAPI()
    app.include_router(mu.MultiUserAdminHttpExtension({}).get_router(None), prefix="/ext")

    @app.get("/v1/default/banks/{bank_id}/documents")
    async def docs(bank_id: str):
        return {"bank": bank_id}

    @app.put("/v1/default/banks/{bank_id}")
    async def create(bank_id: str):
        return {"created": bank_id}

    @app.post("/v1/default/banks/{bank_id}/memories")
    async def retain(bank_id: str):
        return {"retained": bank_id}

    @app.get("/v1/default/chunks/{cid}")
    async def chunk(cid: str):
        return {"chunk": cid}

    app.add_middleware(mu.BankOwnershipMiddleware)
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")
    yield mu, client, RequestContext
    await client.aclose()
    await store.pool.execute(f'DROP SCHEMA "{schema}" CASCADE')
    await store.stop()
    mu._store = None


def h(key):
    return {"Authorization": f"Bearer {key}"}


async def make_user(client, name, role="user"):
    u = (await client.post("/ext/admin/users", json={"username": name, "role": role}, headers=h(ADMIN))).json()
    k = (await client.post(f"/ext/admin/users/{u['id']}/keys", json={"name": "k"}, headers=h(ADMIN))).json()
    return u, k


async def test_auth_and_admin_only(env):
    mu, c, _ = env
    assert (await c.get("/v1/default/banks/b/documents")).status_code == 401
    assert (await c.get("/v1/default/banks/b/documents", headers=h("nope"))).status_code == 401
    assert (await c.get("/ext/admin/users", headers=h(ADMIN))).status_code == 200
    _, k = await make_user(c, "alice")
    assert k["key"].startswith("ek_") and "key_hash" not in k
    assert (await c.get("/ext/admin/users", headers=h(k["key"]))).status_code == 403
    assert (await c.get("/ext/admin/users")).status_code == 401


async def test_ownership_isolation(env):
    mu, c, _ = env
    _, ka = await make_user(c, "alice")
    _, kb = await make_user(c, "bob")
    assert (await c.put("/v1/default/banks/a-bank", headers=h(ka["key"]))).status_code == 200
    assert (await c.get("/v1/default/banks/a-bank/documents", headers=h(ka["key"]))).status_code == 200
    # bob cannot read, write, or claim alice's bank
    assert (await c.get("/v1/default/banks/a-bank/documents", headers=h(kb["key"]))).status_code == 404
    assert (await c.post("/v1/default/banks/a-bank/memories", headers=h(kb["key"]))).status_code == 404
    assert (await c.put("/v1/default/banks/a-bank", headers=h(kb["key"]))).status_code == 404
    # an unowned bank cannot be read (only created) by a user
    assert (await c.get("/v1/default/banks/nobody/documents", headers=h(kb["key"]))).status_code == 404
    # admin reaches everything; users cannot use the cross-bank chunk endpoint
    assert (await c.get("/v1/default/banks/a-bank/documents", headers=h(ADMIN))).status_code == 200
    assert (await c.get("/v1/default/chunks/x", headers=h(kb["key"]))).status_code == 403
    assert (await c.get("/v1/default/chunks/x", headers=h(ADMIN))).status_code == 200


async def test_revoke_disable_transfer(env):
    mu, c, _ = env
    ua, ka = await make_user(c, "alice")
    ub, kb = await make_user(c, "bob")
    await c.put("/v1/default/banks/a-bank", headers=h(ka["key"]))
    # transfer to bob
    assert (await c.put("/ext/admin/banks/a-bank/owner", json={"user_id": ub["id"]}, headers=h(ADMIN))).status_code == 200
    assert (await c.get("/v1/default/banks/a-bank/documents", headers=h(kb["key"]))).status_code == 200
    mu.get_store().invalidate()
    assert (await c.get("/v1/default/banks/a-bank/documents", headers=h(ka["key"]))).status_code == 404
    # revoke bob's key
    assert (await c.delete(f"/ext/admin/keys/{kb['id']}", headers=h(ADMIN))).status_code == 204
    assert (await c.get("/v1/default/banks/a-bank/documents", headers=h(kb["key"]))).status_code == 401
    # disable alice
    await c.patch(f"/ext/admin/users/{ua['id']}", json={"disabled": True}, headers=h(ADMIN))
    assert (await c.get("/v1/default/banks/x/documents", headers=h(ka["key"]))).status_code == 401
    # duplicate username
    assert (await c.post("/ext/admin/users", json={"username": "alice"}, headers=h(ADMIN))).status_code == 409


async def test_validator_and_bank_list(env):
    mu, c, RequestContext = env
    from entelechy_api.extensions.operation_validator import BankListContext, BankReadContext, RecallContext

    ua, _ = await make_user(c, "alice")
    ub, _ = await make_user(c, "bob")
    v = mu.OwnershipValidator({})
    ra = RequestContext(user_id=ua["id"])
    rb = RequestContext(user_id=ub["id"])
    assert (await v.validate_bank_read(BankReadContext(bank_id="a", operation="x", request_context=ra))).allowed
    assert not (await v.validate_bank_read(BankReadContext(bank_id="a", operation="x", request_context=rb))).allowed
    # recall never claims
    res = await v.validate_recall(RecallContext(bank_id="zzz", query="q", request_context=ra))
    assert not res.allowed
    banks = [{"bank_id": "a"}, {"bank_id": "b"}]
    assert (await v.filter_bank_list(BankListContext(banks=banks, request_context=ra))).banks == [{"bank_id": "a"}]
    assert (await v.filter_bank_list(BankListContext(banks=banks, request_context=rb))).banks == []
    assert len((await v.filter_bank_list(BankListContext(banks=banks, request_context=RequestContext(is_admin=True)))).banks) == 2
