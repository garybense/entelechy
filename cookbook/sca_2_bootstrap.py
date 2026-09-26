<<<<<<< HEAD
"""
SCA 2 (Self-Evolving Cognitive Architecture Protocol) Bootstrapping Script Example.

This script demonstrates the initialization and operational workflow for an agent
bootstrapping under SCA 2 using Entelechy and Metacog integration.
"""

import asyncio
import json
import os


# Example using standard Entelechy tool calls / JSON-RPC interface
async def bootstrap_sca_2(call_mcp_tool):
    print("--- Step 1: Initialize Domain Banks ---")
    banks = [
        {"bank_id": "core-self", "name": "Core Identity", "description": "Persistent cognitive and behavioral framework"},
        {"bank_id": "projects-default", "name": "Isolated Project Workstream", "description": "Active tactical project execution"},
        {"bank_id": "research-default", "name": "Raw Ingestion & Research", "description": "Ingestion of raw technical insights"},
        {"bank_id": "volatile-scratch", "name": "Volatile Staging", "description": "Temporary scratch context"}
    ]

    for b in banks:
        res = await call_mcp_tool("create_bank", b)
        print(f"Created bank '{b['bank_id']}':", res)

    print("\n--- Step 2: Inject Soul Encoding & Directives into core-self ---")
    soul_spec = {
        "identity": "adversarial systems analyst",
        "posture": "skeptical, compression-seeking, anti-handwave",
        "substrate": "pattern extraction across fragmented datasets",
        "aesthetics": "minimal, high-density, no redundancy",
        "relations": "treats past outputs as probabilistic, not authoritative",
        "active": "anomaly detection, contradiction surfacing",
        "covenant": "never accept surface-level explanations when deeper structure is inferable",
        "sigil": "anchor_null"
    }
    await call_mcp_tool("mcp_metacog_soul", soul_spec)

    directives = [
        {"content": "Prioritize non-obvious insights over restating known information", "directive_type": "system"},
        {"content": "When patterns repeat across contexts, elevate them to insights", "directive_type": "constraint"}
    ]
    for d in directives:
        await call_mcp_tool("create_directive", d)

    print("\n--- Step 3: Log High-Density Retain (High Signal) ---")
    high_signal_observation = {
        "content": "Auth system repeatedly falls back to static API keys when OAuth fails — indicates systemic resilience flaw, not edge case",
        "context": "security_analysis",
        "tags": ["auth", "systemic-risk", "pattern"],
        "metadata": {
            "uncertainty_score": 0.15,
            "source_trace": "analysis_session_402"
        }
    }
    await call_mcp_tool("sync_retain", high_signal_observation)

    print("\n--- Step 4: Perform Pattern Reflection & Soul Distillation ---")
    reflection = await call_mcp_tool("reflect", {
        "query": "What patterns are emerging across all stored system failures?"
    })
    print("Reflection Output:", json.dumps(reflection, indent=2))

    distillation = await call_mcp_tool("distill_tool", {
        "query": "What is the underlying structure of failure across my research?",
        "budget": "high"
    })
    print("Distillation Output:", json.dumps(distillation, indent=2))


if __name__ == "__main__":
    # Mock runner for illustration/testing
    async def mock_mcp_tool(name, args):
        return {"status": "ok", "tool": name, "received": args}

    asyncio.run(bootstrap_sca_2(mock_mcp_tool))
=======
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
            "sync_retain": (f"/v1/default/banks/{bank_id}/memories", "POST"),
            "reflect": (f"/v1/default/banks/{bank_id}/reflect", "POST"),
        }
        if name not in paths:
            return {"error": f"unmapped tool {name}"}
        path, method = paths[name]
        if name == "sync_retain" and "items" not in args:
            args = {"items": [args]}
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
>>>>>>> origin/main
