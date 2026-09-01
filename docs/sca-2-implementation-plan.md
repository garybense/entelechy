# SCA-2 Implementation Plan (v2 — easter-egg reframe)

**Decision (2026-08-31):** Metacog — the soul layer, the 8-step cycle, feel/drugs/become/name/
ritual/molt/compass/commune/listen, souls, sigils, presets — is an **undocumented easter egg**, not
a product feature. It stays implemented in `engine/metacog/` and `engine/soul/` but:

- **invisible via MCP by default** (all of it, including `encode_soul`/`get_soul`/`list_soul_lineage`/`distill_tool`, which are currently in the default toolset);
- **no HTTP/REST surface, ever** — no OpenAPI, no generated SDK methods, no control-plane UI;
- **no public docs** — the cycle/glossary resources become the *reward* for finding the egg;
- unlocked only by a **secret onboarding bootstrapper** (in-theme trigger → flips the per-bank tool
  filter → returns the hidden resources).

SCA-2 (the public, supported product layer) is mystic-free: bank taxonomy, high-signal retain
discipline, recall-vs-reflect routing, directives, reasoning-traces-plus-uncertainty.

**Execution model:** Fable writes explicit specs → Jules implements → Fable reviews the scoped
diff. Specs live in `docs/jules-spec-*.md`.

## Verified ground truth (2026-08-31)

- `engine/metacog/*` is implemented but **registered nowhere** (absent from `_ALL_TOOLS`,
  `entelechy-api-slim/entelechy_api/mcp_tools.py:29`; no HTTP routes).
- Yet `api/mcp.py` **advertises the whole cycle to every connecting agent** via
  `_SERVER_INSTRUCTIONS`, `_START_HERE_PAYLOAD`, `_CYCLE_RESOURCE`, `_GLOSSARY_RESOURCE`,
  `_QUICKSTART_RESOURCE`. The secret is printed on the front door of a room that doesn't exist.
  This is the #1 leak and the #1 broken-first-impression bug (agents call `feel` → tool not found).
- The soul tools ARE registered and enabled by default (`_ALL_TOOLS` lines 61–64) — the opposite of
  hidden.
- Per-bank tool filtering **already exists** (`_get_enabled_tools()` + bank-config tool ceiling +
  `filter_mcp_tools` validator, `api/mcp.py` ~374–401, `mcp_tools.py` ~374–387). The secret
  bootstrapper needs no new mechanism — just a flag flip.
- The SCA-2 artifacts live on `origin/jules-sca-2-operating-procedure-9147804676413251107`
  (4 relevant files in a 250-file diff that must **never be merged wholesale** — it deletes
  `svt-pipeline-visualizer.tsx`, client `sessions`/`bootstrap` surfaces, ~709 lines of openapi.json).
- Every tool call in those artifacts fails against real signatures (6 defects — see the Jules spec).
- `api/http.py` registers `POST .../sessions/bootstrap` twice (`api_bootstrap_session` at ~2894 and
  ~2953); the second is dead code.
- `engine/metacog/state.py` is a process-local ring buffer; its docstring claims memory-backed
  durability that `get_recent_state()` never implements. Identity reconstructs differently per
  worker/restart.

## Phases

### Phase 0 — Seal the leak + land corrected SCA-2 docs  → `docs/jules-spec-sca2-phase-0.md`
1. Replace the five onboarding constants in `api/mcp.py` with plain memory-product copy
   (retain/recall/reflect, banks, directives, mental models). Remove the three `entelechy://`
   resource registrations. Keep `start_here`.
2. Cherry-pick the 4 SCA-2 files from the Jules branch; rewrite the guide mystic-free; fix all
   6 defective calls; fix the user-guide link.
3. Rewrite `cookbook/sca_2_bootstrap.py`: correct signatures, idempotent, assertive, lints clean.
4. Add `tests/test_sca2_onboarding_consistency.py` — every tool named in onboarding payloads must
   be registered. Permanent fix for the advertise-nonexistent-tools bug class.
5. Delete the duplicate `sessions/bootstrap` route.

### Phase 1 — Hide the soul tools (small, needs care — Fable specs after Phase 0 review)
- Remove `encode_soul`/`get_soul`/`list_soul_lineage`/`distill_tool` from the **default** enabled
  set while keeping them registered; gate behind a bank-config flag (e.g. `metacog_enabled`) using
  the existing tool-filter ceiling. Add the hierarchical config field per CLAUDE.md procedure.
- Fix `state.py` durability: `get_recent_state()` falls back to tag-scoped memory query
  (`metacog:state:{tool}`) when the buffer is cold.

### Phase 2 — The secret bootstrapper (design first; it's the fun part)
- Register metacog primitives as MCP tools (pattern: `engine/soul/mcp_tools.py`), **excluded from
  every default toolset** — visible only when the bank flag is set.
- In-theme unlock trigger (candidate: an undocumented invocation phrase via a specific
  retain/mission string, or a hidden tool) → sets the flag → returns `entelechy://cycle` etc. as
  the reward. These resources are served **only** to unlocked banks.
- Register `name` as `true_name` (too generic otherwise).

### Phase 3 — SCA-2 product layer (public, supported)
- 4-tier bank taxonomy as **bank templates** (`BankTemplateManifest` + `POST .../import` already
  exist and are idempotent): `core-self`, `project:<slug>`, `research:<slug>`, `volatile`
  (colon convention matches existing `channel:` prefix; `/` breaks URL path segments).
- One idempotent `bootstrap_sca2` MCP tool with `dry_run`. `start_here(mode="sca2")`.
- Enforcement: high-signal retain strategy (reject filler in `core-self`, warn in project/research,
  accept in volatile); reserved metadata keys `sca2:uncertainty`, `sca2:trace`, `sca2:supersedes`
  (stringified — `metadata` is `dict[str,str]`); volatile decay via `engine/srl/decay.py`.

### Phase 4 — Self-evolving roadmap (design docs first, in dependency order)
temporal weighting → contradiction tracking (`sca2:contradiction` links + register mental model;
surface, never auto-resolve) → cross-bank federated reflect (fan-out + existing RRF fusion;
isolation stays strict, explicit bank list per request) → belief revision that **proposes** a molt
and never auto-commits identity.

## Standing rules
- Never merge a Jules branch; cherry-pick named files only, verify with `git diff --stat --cached`.
- Every PR: `./scripts/hooks/lint.sh`, `uv run ty check entelechy_api/`, `uv run pytest tests/`,
  `/code-review` clean. `./scripts/generate-openapi.sh` only if an HTTP endpoint changed (Phases
  0–2 change none).
- No changelog "Unreleased" entries (release script owns changelogs).
- Metacog vocabulary never appears in: OpenAPI, SDKs, control plane, public docs, default MCP
  onboarding. Grep-gate candidate for CI later.
