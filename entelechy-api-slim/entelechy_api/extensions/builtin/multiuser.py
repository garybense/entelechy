"""
Multi-user extension: users, per-user API keys, and bank ownership.

All users share one schema (the standard design for many users: no per-user
schemas). Every Entelechy table is keyed by ``bank_id``, so isolation is enforced
by *bank ownership*: each bank belongs to one user, a user can only reach their
own banks, and the admin (the shared ``ENTELECHY_API_TENANT_API_KEY``) can reach
every bank and manage users.

Enable with:
    ENTELECHY_API_TENANT_EXTENSION=entelechy_api.extensions.builtin.multiuser:MultiUserTenantExtension
    ENTELECHY_API_OPERATION_VALIDATOR_EXTENSION=entelechy_api.extensions.builtin.multiuser:OwnershipValidator
    ENTELECHY_API_HTTP_EXTENSION=entelechy_api.extensions.builtin.multiuser:MultiUserAdminHttpExtension
    ENTELECHY_API_TENANT_API_KEY=<admin key>

Bank ids are global: the first user to retain into or create a bank id owns it.
User keys are stored as SHA-256 hashes; the plaintext is shown once at creation.
Revoking a key or disabling a user takes effect within AUTH_CACHE_TTL seconds.
"""

import hashlib
import hmac
import logging
import re
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Any

import asyncpg
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from entelechy_api.config import get_config
from entelechy_api.extensions.http import HttpExtension
from entelechy_api.extensions.operation_validator import (
    BankListContext,
    BankListResult,
    OperationValidatorExtension,
    ValidationResult,
)
from entelechy_api.extensions.tenant import AuthenticationError, Tenant, TenantContext, TenantExtension
from entelechy_api.models import RequestContext

logger = logging.getLogger(__name__)

AUTH_CACHE_TTL = 30.0
KEY_PREFIX = "ek_"
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.@-]{1,64}$")
ROLES = ("user", "admin")


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_key() -> tuple[str, str]:
    """Return (plaintext key, display prefix)."""
    body = secrets.token_urlsafe(32)
    return f"{KEY_PREFIX}{body}", f"{KEY_PREFIX}{body[:6]}"


@dataclass
class Principal:
    """Who a request is: the shared admin key, or a user (optionally a user with role admin)."""

    is_admin: bool
    user_id: str | None = None
    username: str | None = None
    key_id: str | None = None


class UserStore:
    """Users, API keys and bank owners, in the configured schema."""

    def __init__(self, dsn: str, schema: str, admin_key: str):
        self._dsn = re.sub(r"^postgres(ql)?\+\w+://", r"postgresql://", dsn)
        self._schema = schema
        self._admin_key = admin_key
        self._pool: asyncpg.Pool | None = None
        self._cache: dict[str, tuple[float, Principal | None]] = {}

    def _t(self, name: str) -> str:
        return f'"{self._schema}".{name}'

    async def start(self) -> None:
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)
        async with self._pool.acquire() as c:
            await c.execute(f'CREATE SCHEMA IF NOT EXISTS "{self._schema}"')
            await c.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._t("eu_users")} (
                    id uuid PRIMARY KEY,
                    username text NOT NULL UNIQUE,
                    display_name text,
                    org text,
                    role text NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
                    disabled boolean NOT NULL DEFAULT false,
                    created_at timestamptz NOT NULL DEFAULT now()
                );
                CREATE TABLE IF NOT EXISTS {self._t("eu_api_keys")} (
                    id uuid PRIMARY KEY,
                    user_id uuid NOT NULL REFERENCES {self._t("eu_users")}(id) ON DELETE CASCADE,
                    name text NOT NULL,
                    prefix text NOT NULL,
                    key_hash text NOT NULL UNIQUE,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    last_used_at timestamptz,
                    revoked_at timestamptz
                );
                CREATE INDEX IF NOT EXISTS eu_api_keys_user ON {self._t("eu_api_keys")}(user_id);
                CREATE TABLE IF NOT EXISTS {self._t("eu_bank_owners")} (
                    bank_id text PRIMARY KEY,
                    user_id uuid NOT NULL REFERENCES {self._t("eu_users")}(id) ON DELETE CASCADE,
                    created_at timestamptz NOT NULL DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS eu_bank_owners_user ON {self._t("eu_bank_owners")}(user_id);
                """
            )

    async def stop(self) -> None:
        if self._pool:
            await self._pool.close()

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("UserStore not started")
        return self._pool

    # ---- authentication -------------------------------------------------
    async def authenticate(self, key: str | None) -> Principal:
        if not key:
            raise AuthenticationError("API key required")
        if self._admin_key and hmac.compare_digest(key, self._admin_key):
            return Principal(is_admin=True, username="admin")
        h = hash_key(key)
        now = time.monotonic()
        hit = self._cache.get(h)
        if hit and now - hit[0] < AUTH_CACHE_TTL:
            principal = hit[1]
        else:
            row = await self.pool.fetchrow(
                f"""SELECT k.id AS key_id, u.id, u.username, u.role
                    FROM {self._t("eu_api_keys")} k JOIN {self._t("eu_users")} u ON u.id = k.user_id
                    WHERE k.key_hash = $1 AND k.revoked_at IS NULL AND NOT u.disabled""",
                h,
            )
            principal = (
                Principal(
                    is_admin=row["role"] == "admin",
                    user_id=str(row["id"]),
                    username=row["username"],
                    key_id=str(row["key_id"]),
                )
                if row
                else None
            )
            self._cache[h] = (now, principal)
            if row:
                await self.pool.execute(
                    f"UPDATE {self._t('eu_api_keys')} SET last_used_at = now() WHERE id = $1", row["key_id"]
                )
        if principal is None:
            raise AuthenticationError("Invalid API key")
        return principal

    def invalidate(self) -> None:
        self._cache.clear()

    # ---- users ----------------------------------------------------------
    async def create_user(self, username: str, display_name: str | None, org: str | None, role: str) -> dict:
        try:
            row = await self.pool.fetchrow(
                f"""INSERT INTO {self._t("eu_users")} (id, username, display_name, org, role)
                    VALUES ($1,$2,$3,$4,$5) RETURNING *""",
                uuid.uuid4(),
                username,
                display_name,
                org,
                role,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(409, f"User '{username}' already exists") from None
        return _user(row)

    async def list_users(self, org: str | None = None) -> list[dict]:
        rows = await self.pool.fetch(
            f"""SELECT u.*, (SELECT count(*) FROM {self._t("eu_bank_owners")} b WHERE b.user_id = u.id) AS bank_count,
                       (SELECT count(*) FROM {self._t("eu_api_keys")} k
                        WHERE k.user_id = u.id AND k.revoked_at IS NULL) AS key_count
                FROM {self._t("eu_users")} u WHERE ($1::text IS NULL OR u.org = $1) ORDER BY u.created_at""",
            org,
        )
        return [_user(r) for r in rows]

    async def get_user(self, user_id: str) -> dict:
        row = await self.pool.fetchrow(f"SELECT * FROM {self._t('eu_users')} WHERE id = $1", _uuid(user_id))
        if not row:
            raise HTTPException(404, "User not found")
        return _user(row)

    async def update_user(self, user_id: str, fields: dict[str, Any]) -> dict:
        cols = {k: v for k, v in fields.items() if k in ("display_name", "org", "role", "disabled")}
        if not cols:
            return await self.get_user(user_id)
        sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(cols))
        row = await self.pool.fetchrow(
            f"UPDATE {self._t('eu_users')} SET {sets} WHERE id = $1 RETURNING *", _uuid(user_id), *cols.values()
        )
        if not row:
            raise HTTPException(404, "User not found")
        self.invalidate()
        return _user(row)

    async def delete_user(self, user_id: str) -> None:
        res = await self.pool.execute(f"DELETE FROM {self._t('eu_users')} WHERE id = $1", _uuid(user_id))
        if res == "DELETE 0":
            raise HTTPException(404, "User not found")
        self.invalidate()

    # ---- keys -----------------------------------------------------------
    async def create_key(self, user_id: str, name: str) -> dict:
        await self.get_user(user_id)
        key, prefix = generate_key()
        row = await self.pool.fetchrow(
            f"""INSERT INTO {self._t("eu_api_keys")} (id, user_id, name, prefix, key_hash)
                VALUES ($1,$2,$3,$4,$5) RETURNING id, name, prefix, created_at""",
            uuid.uuid4(),
            _uuid(user_id),
            name,
            prefix,
            hash_key(key),
        )
        return {**_plain(row), "key": key}

    async def list_keys(self, user_id: str) -> list[dict]:
        rows = await self.pool.fetch(
            f"""SELECT id, name, prefix, created_at, last_used_at, revoked_at
                FROM {self._t("eu_api_keys")} WHERE user_id = $1 ORDER BY created_at""",
            _uuid(user_id),
        )
        return [_plain(r) for r in rows]

    async def revoke_key(self, key_id: str) -> None:
        res = await self.pool.execute(
            f"UPDATE {self._t('eu_api_keys')} SET revoked_at = now() WHERE id = $1 AND revoked_at IS NULL",
            _uuid(key_id),
        )
        if res == "UPDATE 0":
            raise HTTPException(404, "Key not found or already revoked")
        self.invalidate()

    # ---- bank ownership -------------------------------------------------
    async def owner_of(self, bank_id: str) -> str | None:
        row = await self.pool.fetchrow(f"SELECT user_id FROM {self._t('eu_bank_owners')} WHERE bank_id = $1", bank_id)
        return str(row["user_id"]) if row else None

    async def claim_bank(self, bank_id: str, user_id: str) -> str:
        """Own the bank if nobody does yet. Returns the owner's user id (race-safe)."""
        await self.pool.execute(
            f"INSERT INTO {self._t('eu_bank_owners')} (bank_id, user_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
            bank_id,
            _uuid(user_id),
        )
        owner = await self.owner_of(bank_id)
        assert owner is not None
        return owner

    async def set_owner(self, bank_id: str, user_id: str) -> None:
        await self.get_user(user_id)
        await self.pool.execute(
            f"""INSERT INTO {self._t("eu_bank_owners")} (bank_id, user_id) VALUES ($1,$2)
                ON CONFLICT (bank_id) DO UPDATE SET user_id = EXCLUDED.user_id""",
            bank_id,
            _uuid(user_id),
        )

    async def release_bank(self, bank_id: str) -> None:
        await self.pool.execute(f"DELETE FROM {self._t('eu_bank_owners')} WHERE bank_id = $1", bank_id)

    async def owned_banks(self, user_id: str) -> set[str]:
        rows = await self.pool.fetch(
            f"SELECT bank_id FROM {self._t('eu_bank_owners')} WHERE user_id = $1", _uuid(user_id)
        )
        return {r["bank_id"] for r in rows}

    async def all_owners(self) -> list[dict]:
        rows = await self.pool.fetch(
            f"""SELECT b.bank_id, b.user_id, u.username, b.created_at
                FROM {self._t("eu_bank_owners")} b JOIN {self._t("eu_users")} u ON u.id = b.user_id ORDER BY b.bank_id"""
        )
        return [_plain(r) for r in rows]


def _uuid(v: str) -> uuid.UUID:
    try:
        return uuid.UUID(v)
    except ValueError:
        raise HTTPException(404, "Not found") from None


def _plain(row: Any) -> dict:
    out: dict[str, Any] = {}
    for k, v in dict(row).items():
        if isinstance(v, uuid.UUID):
            out[k] = str(v)
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def _user(row: Any) -> dict:
    return _plain(row)


# One store per process, shared by the tenant, validator and admin extensions.
_store: UserStore | None = None


def get_store() -> UserStore:
    if _store is None:
        raise RuntimeError("Multi-user store not initialised (is MultiUserTenantExtension enabled?)")
    return _store


class MultiUserTenantExtension(TenantExtension):
    """Authenticates the admin key or a per-user key and returns the shared schema."""

    def __init__(self, config: dict[str, str]):
        super().__init__(config)
        self.admin_key = config.get("api_key")
        if not self.admin_key:
            raise ValueError("ENTELECHY_API_TENANT_API_KEY (the admin key) is required for MultiUserTenantExtension")

    async def on_startup(self) -> None:
        global _store
        cfg = get_config()
        _store = UserStore(cfg.database_url, cfg.database_schema, self.admin_key or "")
        await _store.start()
        logger.info("Multi-user store ready (schema %s)", cfg.database_schema)

    async def on_shutdown(self) -> None:
        if _store:
            await _store.stop()

    async def authenticate(self, context: RequestContext) -> TenantContext:
        try:
            principal = await get_store().authenticate(context.api_key)
        except AuthenticationError:
            raise
        context.is_admin = principal.is_admin
        context.user_id = principal.user_id
        context.api_key_id = principal.key_id
        context.tenant_id = principal.username
        return TenantContext(schema_name=get_config().database_schema)

    async def authenticate_mcp(self, context: RequestContext) -> TenantContext:
        return await self.authenticate(context)

    async def list_tenants(self) -> list[Tenant]:
        return [Tenant(schema=get_config().database_schema)]


class OwnershipValidator(OperationValidatorExtension):
    """Rejects operations on banks the caller does not own; the admin passes everywhere."""

    CLAIMING = {"retain", "bank_read", "bank_write"}

    async def _check(self, ctx: Any, op: str) -> ValidationResult:
        rc: RequestContext = ctx.request_context
        if rc.internal or rc.is_admin:
            return ValidationResult.accept()
        if not rc.user_id:
            return ValidationResult.reject("Authentication required", 401)
        store = get_store()
        owner = await store.owner_of(ctx.bank_id)
        if owner is None and op in self.CLAIMING:
            owner = await store.claim_bank(ctx.bank_id, rc.user_id)
        if owner != rc.user_id:
            # Same answer for "not yours" and "does not exist": do not reveal other users' bank ids.
            return ValidationResult.reject(f"Bank '{ctx.bank_id}' not found", 404)
        return ValidationResult.accept()

    async def validate_retain(self, ctx):
        return await self._check(ctx, "retain")

    async def validate_recall(self, ctx):
        return await self._check(ctx, "recall")

    async def validate_reflect(self, ctx):
        return await self._check(ctx, "reflect")

    async def validate_consolidate(self, ctx):
        return await self._check(ctx, "consolidate")

    async def validate_mental_model_get(self, ctx):
        return await self._check(ctx, "mental_model_get")

    async def validate_mental_model_refresh(self, ctx):
        return await self._check(ctx, "mental_model_refresh")

    async def validate_bank_read(self, ctx):
        return await self._check(ctx, "bank_read")

    async def validate_bank_write(self, ctx):
        return await self._check(ctx, "bank_write")

    async def filter_bank_list(self, ctx: BankListContext) -> BankListResult:
        rc = ctx.request_context
        if rc.internal or rc.is_admin:
            return BankListResult(banks=ctx.banks)
        if not rc.user_id:
            return BankListResult(banks=[])
        owned = await get_store().owned_banks(rc.user_id)
        return BankListResult(banks=[b for b in ctx.banks if b.get("bank_id") in owned])


# ---- admin HTTP API (/ext/admin/...) ----------------------------------------


class NewUser(BaseModel):
    username: str
    display_name: str | None = None
    org: str | None = None
    role: str = "user"


class UserPatch(BaseModel):
    display_name: str | None = None
    org: str | None = None
    role: str | None = None
    disabled: bool | None = None


class NewKey(BaseModel):
    name: str = Field(default="default", max_length=100)


class OwnerBody(BaseModel):
    user_id: str


async def _require_admin(authorization: str | None) -> Principal:
    key = None
    if authorization:
        key = authorization[7:].strip() if authorization.lower().startswith("bearer ") else authorization.strip()
    try:
        principal = await get_store().authenticate(key)
    except AuthenticationError as e:
        raise HTTPException(401, e.reason) from None
    if not principal.is_admin:
        raise HTTPException(403, "Admin only")
    return principal


class MultiUserAdminHttpExtension(HttpExtension):
    """User, key and bank-ownership administration. Admin credentials only."""

    def get_router(self, memory: Any) -> APIRouter:
        router = APIRouter(prefix="/admin", tags=["Admin"])

        @router.get("/users")
        async def list_users(org: str | None = None, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            return {"users": await get_store().list_users(org)}

        @router.post("/users", status_code=201)
        async def create_user(body: NewUser, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            if not USERNAME_RE.match(body.username):
                raise HTTPException(422, "username must be 1-64 chars of letters, digits, _ . @ -")
            if body.role not in ROLES:
                raise HTTPException(422, f"role must be one of {ROLES}")
            return await get_store().create_user(body.username, body.display_name, body.org, body.role)

        @router.get("/users/{user_id}")
        async def get_user(user_id: str, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            store = get_store()
            user = await store.get_user(user_id)
            return {**user, "keys": await store.list_keys(user_id), "banks": sorted(await store.owned_banks(user_id))}

        @router.patch("/users/{user_id}")
        async def patch_user(user_id: str, body: UserPatch, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            if body.role is not None and body.role not in ROLES:
                raise HTTPException(422, f"role must be one of {ROLES}")
            return await get_store().update_user(user_id, body.model_dump(exclude_unset=True))

        @router.delete("/users/{user_id}", status_code=204)
        async def delete_user(user_id: str, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            await get_store().delete_user(user_id)

        @router.post("/users/{user_id}/keys", status_code=201)
        async def create_key(user_id: str, body: NewKey, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            return await get_store().create_key(user_id, body.name)  # includes plaintext "key" once

        @router.delete("/keys/{key_id}", status_code=204)
        async def revoke_key(key_id: str, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            await get_store().revoke_key(key_id)

        @router.get("/banks")
        async def list_bank_owners(authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            return {"owners": await get_store().all_owners()}

        @router.put("/banks/{bank_id}/owner")
        async def set_owner(bank_id: str, body: OwnerBody, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            await get_store().set_owner(bank_id, body.user_id)
            return {"bank_id": bank_id, "user_id": body.user_id}

        @router.delete("/banks/{bank_id}/owner", status_code=204)
        async def release_bank(bank_id: str, authorization: str | None = Header(default=None)):
            await _require_admin(authorization)
            await get_store().release_bank(bank_id)

        return router


# ---- REST enforcement ---------------------------------------------------------

_BANK_PATH = re.compile(r"^/v1/default/banks/([^/]+)(/.*)?$")


class BankOwnershipMiddleware:
    """
    ASGI middleware: authenticates every /v1 request and enforces bank ownership on
    /v1/default/banks/{bank_id}/**. Many bank-scoped endpoints (documents, entities,
    graph, ...) do not call the operation validator, so ownership is checked here,
    uniformly, from the URL. Admins pass; users reach only banks they own.

    Not bank-scoped but cross-bank, so admin-only for users: /v1/default/chunks/{id}.
    """

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        path = scope.get("path", "")
        if scope["type"] != "http" or not path.startswith("/v1/") or scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        auth = headers.get("authorization")
        key = None
        if auth:
            key = auth[7:].strip() if auth.lower().startswith("bearer ") else auth.strip()
        try:
            principal = await get_store().authenticate(key)
        except AuthenticationError as e:
            await _json(send, 401, {"detail": e.reason})
            return

        if principal.is_admin:
            await self.app(scope, receive, send)
            return

        if path.startswith("/v1/default/chunks/"):
            await _json(send, 403, {"detail": "Admin only"})
            return

        m = _BANK_PATH.match(path)
        if m and principal.user_id:
            bank_id, rest = m.group(1), m.group(2) or ""
            store = get_store()
            owner = await store.owner_of(bank_id)
            creates = (
                (scope["method"] == "PUT" and rest == "")
                or (scope["method"] == "POST" and rest.rstrip("/") == "/memories")
                or (scope["method"] == "GET" and rest.rstrip("/") == "/profile")
            )
            if owner is None and creates:
                owner = await store.claim_bank(bank_id, principal.user_id)
            if owner != principal.user_id:
                await _json(send, 404, {"detail": f"Bank '{bank_id}' not found"})
                return

        await self.app(scope, receive, send)


async def _json(send: Any, status: int, body: dict) -> None:
    import json

    payload = json.dumps(body).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode())],
        }
    )
    await send({"type": "http.response.body", "body": payload})
