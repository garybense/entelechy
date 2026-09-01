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
