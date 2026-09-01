# Jules Spec — SCA-2 Phase 0: seal the metacog leak, land corrected SCA-2 docs

Follow this spec **exactly**. Do not add features, do not refactor neighboring code, do not touch
any file not listed in "Files you may modify". Do not regenerate clients or OpenAPI. When a step
says "replace with the following", use the text verbatim.

## Branch & scope rules

- Create branch `sca2/phase-0` from latest `origin/main`.
- **Files you may modify (complete list):**
  1. `entelechy-api-slim/entelechy_api/api/mcp.py`
  2. `entelechy-api-slim/entelechy_api/api/http.py` (one deletion only, Task 5)
  3. `entelechy-docs/guides/2026-05-01-guide-sca-2-self-evolving-cognitive-architecture.md` (new)
  4. `cookbook/sca_2_bootstrap.py` (new)
  5. `cookbook/README.md`
  6. `ENTELECHY_USER_GUIDE.md`
  7. `entelechy-api-slim/tests/test_sca2_onboarding_consistency.py` (new)
- If your diff touches ANY other file, revert that file before pushing.
- Do NOT merge or cherry-pick commits from branch
  `jules-sca-2-operating-procedure-9147804676413251107`. Only the file *contents* specified below.

---

## Task 1 — De-advertise metacog in `entelechy-api-slim/entelechy_api/api/mcp.py`

The module currently defines five onboarding constants that describe metacog/soul features
(`feel`, `drugs`, `become`, `name`, `ritual`, `molt`, `compass`, `commune`, `listen`, souls,
sigils, SRL, MWPM). These features must not be mentioned to connecting agents.

### 1a. Replace `_SERVER_INSTRUCTIONS` (entire constant) with:

```python
_SERVER_INSTRUCTIONS = """\
You are connected to Entelechy — long-term memory for AI agents.

Memory operations are bank-scoped. A bank is one agent's isolated memory store. \
Each operation that takes a bank_id is isolated to that bank.

Core operations:
- retain  — store a memory (decisions, discoveries, compressed observations)
- recall  — retrieve stored facts and fragments
- reflect — reason across memories to extract patterns and answer questions

If you don't know where to begin, call the `start_here` tool first. It returns \
a structured onboarding payload: a routing table mapping intents to tools and a \
quickstart sequence for first-time and returning agents.
"""
```

### 1b. Replace `_START_HERE_PAYLOAD` (entire constant) with:

```python
_START_HERE_PAYLOAD = {
    "name": "Entelechy",
    "what": "Long-term memory for AI agents: multi-strategy retrieval, reasoning over memories, and per-bank directives.",
    "routing_table": {
        "I want to remember something": "retain (or sync_retain for synchronous)",
        "I want to find facts": "recall",
        "I want to reason across memories": "reflect",
        "I want to add a hard rule": "create_directive",
        "I want a pinned reasoning artifact": "create_mental_model",
        "I want to see what's stored": "list_memories / list_documents / list_tags",
    },
    "quickstart": {
        "first_session_for_new_bank": [
            "1. create_bank(bank_id, mission='what this agent attends to')",
            "2. retain(...) experiences as they occur",
            "3. recall / reflect as the work demands",
        ],
        "returning_session_existing_bank": [
            "1. get_bank() — confirm the bank and its mission",
            "2. proceed with normal recall / retain / reflect",
        ],
    },
    "retention_discipline": (
        "Store decisions, discoveries, contradictions, and compressed observations. "
        "Do not store conversational filler or obvious facts. Always provide context and tags."
    ),
}
```

### 1c. Delete constants and resources

- Delete the constants `_CYCLE_RESOURCE`, `_GLOSSARY_RESOURCE`, `_QUICKSTART_RESOURCE` entirely.
- In `_register_onboarding()`: keep the `start_here` tool registration; delete the three
  `@mcp.resource(...)` registrations (`entelechy://cycle`, `entelechy://glossary`,
  `entelechy://quickstart`) and their functions.
- Update the module comment block above `_SERVER_INSTRUCTIONS` and the `start_here` docstring so
  they no longer mention the deleted resources, the "8-step cycle", SRL, or MWPM. Remove the
  `"deeper_resources"` key if you kept it anywhere (1b above already omits it).
- Update the `_register_onboarding` docstring accordingly.

### 1d. What NOT to change in this file

- Do not touch tool registration, auth, middleware, `_make_tools_tolerant`, `_SINGLE_BANK_TOOLS`,
  or anything below `_register_onboarding`.
- Do not remove any tools from `_ALL_TOOLS` in `mcp_tools.py` (that file is out of scope).

---

## Task 2 — Create the SCA-2 guide

Create `entelechy-docs/guides/2026-05-01-guide-sca-2-self-evolving-cognitive-architecture.md`
with EXACTLY this content:

````markdown
---
title: "SCA-2: Self-Evolving Cognitive Architecture — Operating Procedure"
authors: [benfrank241]
date: 2026-05-01
tags: [how-to, sca-2, cognitive-architecture, memory, directives, onboarding]
description: "An advanced operating procedure and bootstrapping strategy for AI agents using Entelechy as a self-evolving cognitive architecture."
hide_table_of_contents: false
---

**SCA-2** (Self-Evolving Cognitive Architecture, Protocol 2) is an advanced, auxiliary operating
mode for AI agents connected to Entelechy. Rather than treating memory as an unstructured log,
SCA-2 turns Entelechy into a compounding cognition system: domain-isolated banks, high-signal
retention, and aggressive use of `reflect` for cross-temporal pattern extraction.

---

## Operating Principles

### 1. Bank Strategy: Domain-Isolated Memory Taxonomy

Single-bank setups degrade over time: recall and reflect performance decays into semantic noise
when the embedding space is polluted with unrelated domains. Under SCA-2, agents maintain a strict
4-tier bank taxonomy (note: bank ids use `:` as the namespace separator — `/` is not valid in a
bank id):

```
core-self          → identity, governing directives, epistemic posture, long-term philosophy
project:<slug>     → one isolated workstream per bank
research:<slug>    → raw ingestion + insight extraction per domain
volatile           → temporary scratch / staging; nothing here is authoritative
```

### 2. Retain Strategy: High-Signal Only

Most memory systems are destroyed by logging garbage.

* **Store ONLY:** decisions, discoveries, contradictions, compressed observations.
* **Do NOT store:** conversational filler, obvious facts, anything you would not want
  resurfacing later.

A proper retain is dense, reusable, and cross-applicable:

```json
{
  "content": "Auth system repeatedly falls back to static API keys when OAuth fails — indicates systemic resilience flaw, not edge case",
  "context": "security_analysis",
  "tags": ["auth", "systemic-risk", "pattern"],
  "metadata": {
    "sca2:uncertainty": "0.15",
    "sca2:trace": "analysis_session_402"
  }
}
```

Note: `metadata` values must be strings.

### 3. Recall vs. Reflect

* **`recall`** when you think something already exists and you want fragments: exact parameters,
  prior decisions, historic snippets.
* **`reflect`** when you want pattern extraction or suspect hidden structure across time:
  cross-temporal analysis of failures, anomalies, emergent structure.

If you underuse `reflect`, you are running a vector database and calling it intelligence.

### 4. The Mirror Mechanism: Traces, Not Conclusions

Past-you becomes a high-trust external signal. That cuts both ways: it can bootstrap epistemic
stability, or lock you into recursive delusion. The difference is what you store.

* **Risk:** storing bare conclusions leads to self-reinforcing cognitive lock-in.
* **SCA-2 rule:** always store **reasoning traces + uncertainty** alongside conclusions, using the
  reserved metadata keys `sca2:uncertainty` (stringified 0–1) and `sca2:trace`. This preserves the
  ability to revise beliefs later.

### 5. Honest Limits

Even with perfect use, outputs are bounded by embedding fidelity, retrieval bias, and prompt
interpretation. Treat them as structured reconstructions constrained by your past thinking — a
strong prior, never verified fact. The single discipline that prevents recursive delusion is rule 4.

---

## Step-by-Step Initialization

### Step 1 — Initialize the core identity bank

```python
create_bank(
    bank_id="core-self",
    name="Core Identity",
    mission="Persistent cognitive and behavioral framework: identity, directives, epistemic posture. High-signal only.",
)
```

### Step 2 — Inject governing directives

```python
create_directive(
    name="sca2-non-obvious-first",
    content="Prioritize non-obvious insights over restating known information.",
    priority=100,
    tags=["sca2:system"],
    bank_id="core-self",
)

create_directive(
    name="sca2-elevate-repeats",
    content="When patterns repeat across contexts, elevate them to insights.",
    priority=90,
    tags=["sca2:constraint"],
    bank_id="core-self",
)
```

### Step 3 — Create the working banks

```python
create_bank(bank_id="project:default", name="Default Project",
            mission="Active tactical execution for the default workstream.")
create_bank(bank_id="research:default", name="Default Research",
            mission="Raw ingestion and insight extraction.")
create_bank(bank_id="volatile", name="Volatile Staging",
            mission="Temporary scratch. Nothing here is authoritative.")
```

### Step 4 — Build the pattern lattice

Ingest high-density observations (not logs) into the appropriate banks with `retain`, always with
`context`, `tags`, and the `sca2:*` metadata keys. Periodically run pattern reflection:

```python
reflect(
    query="What patterns are emerging across all stored system failures?",
    bank_id="research:default",
)
```

---

## Roadmap

Future SCA-2 extensions: cross-bank reasoning (federated reflect with strict isolation),
contradiction tracking, supervised belief revision, and temporal weighting of memories.
````

---

## Task 3 — Create `cookbook/sca_2_bootstrap.py`

Create with EXACTLY this content:

```python
"""SCA-2 (Self-Evolving Cognitive Architecture, Protocol 2) bootstrap example.

Demonstrates the SCA-2 initialization sequence against a live Entelechy MCP
endpoint, or against a built-in mock with --dry-run. Idempotent: safe to
re-run (create_bank is create-or-get; directives are matched by name upstream).

Usage:
    python sca_2_bootstrap.py --dry-run
    ENTELECHY_API_URL=http://localhost:8000 ENTELECHY_API_KEY=... python sca_2_bootstrap.py
"""

import argparse
import asyncio
import json
import os
import sys

BANKS = [
    {
        "bank_id": "core-self",
        "name": "Core Identity",
        "mission": (
            "Persistent cognitive and behavioral framework: identity, directives, "
            "epistemic posture. High-signal only."
        ),
    },
    {
        "bank_id": "project:default",
        "name": "Default Project",
        "mission": "Active tactical execution for the default workstream.",
    },
    {
        "bank_id": "research:default",
        "name": "Default Research",
        "mission": "Raw ingestion and insight extraction.",
    },
    {
        "bank_id": "volatile",
        "name": "Volatile Staging",
        "mission": "Temporary scratch. Nothing here is authoritative.",
    },
]

DIRECTIVES = [
    {
        "name": "sca2-non-obvious-first",
        "content": "Prioritize non-obvious insights over restating known information.",
        "priority": 100,
        "tags": ["sca2:system"],
        "bank_id": "core-self",
    },
    {
        "name": "sca2-elevate-repeats",
        "content": "When patterns repeat across contexts, elevate them to insights.",
        "priority": 90,
        "tags": ["sca2:constraint"],
        "bank_id": "core-self",
    },
]

HIGH_SIGNAL_EXAMPLE = {
    "content": (
        "Auth system repeatedly falls back to static API keys when OAuth fails — "
        "indicates systemic resilience flaw, not edge case"
    ),
    "context": "security_analysis",
    "tags": ["auth", "systemic-risk", "pattern"],
    "metadata": {"sca2:uncertainty": "0.15", "sca2:trace": "analysis_session_402"},
    "bank_id": "research:default",
}


def _fail(step: str, result: object) -> None:
    print(f"FAILED at {step}: {json.dumps(result, default=str)}")
    sys.exit(1)


def _check(step: str, result: object) -> None:
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            pass
    if isinstance(result, dict) and ("error" in result or result.get("status") == "error"):
        _fail(step, result)
    print(f"ok: {step}")


async def bootstrap_sca_2(call_mcp_tool) -> None:
    print("--- Step 1+3: Initialize domain banks ---")
    for bank in BANKS:
        _check(f"create_bank({bank['bank_id']})", await call_mcp_tool("create_bank", bank))

    print("--- Step 2: Inject governing directives into core-self ---")
    for directive in DIRECTIVES:
        _check(
            f"create_directive({directive['name']})",
            await call_mcp_tool("create_directive", directive),
        )

    print("--- Step 4: High-signal retain + pattern reflection ---")
    _check("sync_retain", await call_mcp_tool("sync_retain", HIGH_SIGNAL_EXAMPLE))
    _check(
        "reflect",
        await call_mcp_tool(
            "reflect",
            {
                "query": "What patterns are emerging across all stored system failures?",
                "bank_id": "research:default",
            },
        ),
    )
    print("SCA-2 bootstrap complete.")


async def _mock_mcp_tool(name: str, args: dict) -> dict:
    return {"status": "ok", "tool": name, "received": args}


def _make_http_caller(base_url: str, api_key: str):
    import urllib.request

    async def call(name: str, args: dict) -> dict:
        args = dict(args)
        bank_id = args.pop("bank_id", "default")
        paths = {
            "create_bank": (f"/v1/default/banks/{bank_id}", "PUT"),
            "create_directive": (f"/v1/default/banks/{bank_id}/directives", "POST"),
            "sync_retain": (f"/v1/default/banks/{bank_id}/memories/retain?sync=true", "POST"),
            "reflect": (f"/v1/default/banks/{bank_id}/reflect", "POST"),
        }
        if name not in paths:
            return {"error": f"unmapped tool {name}"}
        path, method = paths[name]
        req = urllib.request.Request(
            base_url.rstrip("/") + path,
            data=json.dumps(args).encode(),
            method=method,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        )
        loop = asyncio.get_running_loop()

        def _do():
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read() or b"{}")

        try:
            return await loop.run_in_executor(None, _do)
        except Exception as exc:  # noqa: BLE001 — surface any transport error as a result
            return {"error": str(exc)}

    return call


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Use the built-in mock transport")
    args = parser.parse_args()

    if args.dry_run:
        caller = _mock_mcp_tool
    else:
        base_url = os.environ.get("ENTELECHY_API_URL")
        api_key = os.environ.get("ENTELECHY_API_KEY", "")
        if not base_url:
            print("Set ENTELECHY_API_URL (and ENTELECHY_API_KEY), or pass --dry-run.")
            sys.exit(2)
        caller = _make_http_caller(base_url, api_key)

    asyncio.run(bootstrap_sca_2(caller))


if __name__ == "__main__":
    main()
```

IMPORTANT: verify the HTTP paths in `_make_http_caller` against the actual routes in
`entelechy-api-slim/entelechy_api/api/http.py` (search for `banks/{bank_id}` route decorators for
bank create/update, directives, retain, reflect) and correct the paths/methods if they differ.
Do not change anything else about the script structure.

---

## Task 4 — Update `cookbook/README.md` and `ENTELECHY_USER_GUIDE.md`

### `cookbook/README.md` — append:

```markdown

## SCA-2 (Self-Evolving Cognitive Architecture, Protocol 2)

- `sca_2_bootstrap.py`: Runnable script demonstrating the SCA-2 initialization sequence —
  domain-isolated banks, governing directives, and high-signal retention. Supports `--dry-run`.
```

### `ENTELECHY_USER_GUIDE.md` — append:

```markdown

---

## 5. Advanced Auxiliary Onboarding Mode: SCA-2

For advanced multi-agent systems and long-lived autonomous agents, Entelechy supports **SCA-2
(Self-Evolving Cognitive Architecture, Protocol 2)** — an opt-in operating procedure:

1. **Domain Bank Initialization**: partition memory into `core-self`, `project:<slug>`,
   `research:<slug>`, and `volatile` banks.
2. **Governing Directives**: inject system constraints into `core-self`.
3. **Pattern Lattice**: retain only high-signal decisions, discoveries, contradictions, and
   compressed observations — always with reasoning traces and uncertainty
   (`sca2:trace`, `sca2:uncertainty` metadata keys).
4. **Pattern Reflection**: periodically run `reflect` to extract cross-temporal structure.

Full operating procedure:
[SCA-2 Guide](entelechy-docs/guides/2026-05-01-guide-sca-2-self-evolving-cognitive-architecture.md)
and `cookbook/sca_2_bootstrap.py`.
```

Do not modify any existing lines in either file — append only.

---

## Task 5 — Delete the dead duplicate route in `api/http.py`

`entelechy-api-slim/entelechy_api/api/http.py` registers
`POST /v1/default/banks/{bank_id}/sessions/bootstrap` TWICE — two `@app.post(...)` decorators with
identical paths, each followed by an `async def api_bootstrap_session(...)`. The first (near line
2887) uses `recall_async` with `Budget.MID`; the second (near line 2946) uses `memory.recall(...)`
and comments like "5-term retrieval via recall abstraction". FastAPI only serves the first;
the second is dead code.

Delete the ENTIRE second registration: from its `@app.post(` decorator through the end of its
function body (its final `raise HTTPException(status_code=500, detail=str(e))`). Delete nothing
else. Confirm afterwards:
`grep -c "async def api_bootstrap_session" entelechy-api-slim/entelechy_api/api/http.py` → must be `1`.

---

## Task 6 — Create `entelechy-api-slim/tests/test_sca2_onboarding_consistency.py`

Create with EXACTLY this content:

```python
"""Onboarding payloads must only reference tools that are actually registered.

Guards against the bug class where MCP handshake instructions advertise tools
(e.g. metacog primitives) that no code registers — connecting agents then call
tools that don't exist as their first action.
"""

import re

from entelechy_api.api.mcp import _SERVER_INSTRUCTIONS, _START_HERE_PAYLOAD
from entelechy_api.mcp_tools import _ALL_TOOLS

# Non-tool vocabulary that may legitimately appear in onboarding text.
_ALLOWED_NON_TOOLS = {
    "start_here",  # registered separately in _register_onboarding
}

_TOOL_TOKEN = re.compile(r"`([a-z_]{3,})`|\b([a-z_]+_[a-z_]+)\b")


def _referenced_tool_names(text: str) -> set[str]:
    """Extract snake_case tokens that look like tool references."""
    names: set[str] = set()
    for backticked, bare in _TOOL_TOKEN.findall(text):
        token = backticked or bare
        # Only flag tokens that collide with tool-name shape: contain an
        # underscore or are known single-word tools.
        if "_" in token or token in {"retain", "recall", "reflect"}:
            names.add(token)
    return names


def _flatten(payload) -> str:
    if isinstance(payload, dict):
        return " ".join(_flatten(v) for v in list(payload.keys()) + list(payload.values()))
    if isinstance(payload, list):
        return " ".join(_flatten(v) for v in payload)
    return str(payload)


def test_server_instructions_reference_only_registered_tools():
    referenced = _referenced_tool_names(_SERVER_INSTRUCTIONS)
    unknown = referenced - _ALL_TOOLS - _ALLOWED_NON_TOOLS
    # Filter to plausible tool names: those matching a registered tool prefix
    # or verbs agents would call. Anything left is an advertised-but-missing tool.
    suspicious = {t for t in unknown if any(t.startswith(p) for p in ("create_", "get_", "list_", "delete_", "encode_", "sync_"))}
    assert not suspicious, f"_SERVER_INSTRUCTIONS advertises unregistered tools: {sorted(suspicious)}"


def test_start_here_payload_references_only_registered_tools():
    text = _flatten(_START_HERE_PAYLOAD)
    referenced = _referenced_tool_names(text)
    unknown = referenced - _ALL_TOOLS - _ALLOWED_NON_TOOLS
    suspicious = {t for t in unknown if any(t.startswith(p) for p in ("create_", "get_", "list_", "delete_", "encode_", "sync_"))}
    assert not suspicious, f"start_here payload advertises unregistered tools: {sorted(suspicious)}"


def test_metacog_vocabulary_absent_from_onboarding():
    """Metacog features are intentionally hidden; onboarding must not leak them."""
    banned = ["feel(", "drugs", "molt", "compass", "commune", "sigil", "soul", "SRL", "MWPM", "bicameral", "ritual"]
    text = _SERVER_INSTRUCTIONS + _flatten(_START_HERE_PAYLOAD)
    leaked = [w for w in banned if w in text]
    assert not leaked, f"Onboarding leaks hidden metacog vocabulary: {leaked}"
```

If a test fails because a payload key you wrote in Task 1 trips the regex, fix the PAYLOAD wording
(not the test) unless the flagged token is genuinely a registered tool.

---

## Verification (run all, in order — all must pass before pushing)

```bash
cd entelechy-api-slim
uv run ruff check . && uv run ruff format --check .
uv run ty check entelechy_api/
uv run pytest tests/test_sca2_onboarding_consistency.py -v
uv run pytest tests/test_mcp_tools.py -v   # existing MCP tests must still pass
cd ..
python cookbook/sca_2_bootstrap.py --dry-run   # must print "SCA-2 bootstrap complete."
./scripts/hooks/lint.sh
git diff --stat main...HEAD    # must list ONLY the 7 files in scope
grep -c "async def api_bootstrap_session" entelechy-api-slim/entelechy_api/api/http.py  # → 1
```

## Out of scope — do NOT do these even if they seem helpful

- Do not register, unregister, rename, or gate any MCP tool.
- Do not modify `mcp_tools.py`, `engine/metacog/*`, `engine/soul/*`, `engine/srl/*`.
- Do not run `generate-openapi.sh` or `generate-clients.sh` (no endpoint signatures change;
  Task 5 removes a duplicate registration of an existing path only).
- Do not touch the control plane, CLI, integrations, or any generated client.
- Do not add changelog entries.
- Do not merge `main` into your branch repeatedly; rebase once at the end if needed.
```
