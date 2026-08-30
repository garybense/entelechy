---
title: "SCA 2: Self-Evolving Cognitive Architecture Protocol & Operating Procedure"
authors: [benfrank241]
date: 2026-05-01
tags: [how-to, metacog, sca-2, cognitive-architecture, memory, directives, onboarding]
description: "A comprehensive operating procedure and bootstrapping strategy for AI agents using Entelechy and Metacog as a self-evolving cognitive architecture."
hide_table_of_contents: false
---

**SCA 2** (Self-Evolving Cognitive Architecture Protocol) is an advanced auxiliary onboarding and operating mode for AI agents connected to Entelechy and Metacog.

Rather than treating memory as a simple key-value store or unstructured log, **SCA 2 transforms Entelechy into a recursive self-conditioning engine**, enabling agents to achieve epistemic stability, cross-domain insight extraction, and autonomous behavioral evolution.

---

## Operating Principles & Architectural Strategy

### 1. Bank Strategy: Domain-Isolated Memory Taxonomy

Single-bank memory setups degrade over time due to semantic noise and embedding space pollution across unrelated domains. Under SCA 2, connected agents maintain a strict 4-tier bank taxonomy:

```
/core-self        → Identity, governing directives, epistemic posture, long-term philosophy
/projects/*       → Isolated workstreams, project-specific context, tactical execution
/research/*       → Raw ingestion, external documentation, reference material, unstructured insights
/volatile         → Temporary scratchpad, active context staging, transient scratch memory
```

### 2. Retain Strategy: High-Signal Ingestion Only

To prevent system degradation from conversational filler or low-density facts, agents following SCA 2 adhere strictly to high-signal retention rules:

* **Store ONLY**:
  * High-density decisions
  * Systemic discoveries
  * Contradictions & edge cases
  * Compressed observations
* **Do NOT Store**:
  * Conversational filler or pleasantries
  * Surface-level facts or obvious information
  * Transient state or unverified fluff

#### Standard High-Signal Retain Schema
```json
{
  "content": "Auth system repeatedly falls back to static API keys when OAuth fails — indicates systemic resilience flaw, not edge case",
  "context": "security_analysis",
  "tags": ["auth", "systemic-risk", "pattern"],
  "metadata": {
    "uncertainty_score": 0.15,
    "source_trace": "analysis_session_402"
  }
}
```

### 3. Recall vs. Reflect Decision Framework

* **Use `recall` when**:
  * Searching for specific known fragments, exact parameters, or historic code snippets.
  * Verifying if a concrete fact already exists in the memory bank.
* **Use `reflect` when**:
  * Performing cross-temporal pattern extraction across stored system failures or observations.
  * Investigating hidden structures or emergent anomalies across project boundaries.
  * Underusing `reflect` reduces the system to a standard vector database rather than an active intelligence engine.

### 4. The Soul Layer (Metacog): Bias & Posture Injection

The Metacog Soul Layer injects system-level bias and operational posture directly into the agent's cognitive loops.

```json
{
  "identity": "adversarial systems analyst",
  "posture": "skeptical, compression-seeking, anti-handwave",
  "substrate": "pattern extraction across fragmented datasets",
  "aesthetics": "minimal, high-density, no redundancy",
  "relations": "treats past outputs as probabilistic, not authoritative",
  "active": "anomaly detection, contradiction surfacing",
  "covenant": "never accept surface-level explanations when deeper structure is inferable",
  "sigil": "anchor_null"
}
```

### 5. The Mirror Mechanism: Reasoning Traces vs. Conclusions

The **Mirror Mechanism** leverages past outputs as high-trust external cognitive signals.
* **Risk**: Storing raw conclusions leads to self-reinforcing cognitive lock-in and recursive delusion.
* **SCA 2 Rule**: Always store **reasoning traces + uncertainty levels** alongside conclusions. This preserves epistemic stability and enables future belief revision.

---

## Step-by-Step Initialization & Onboarding Sequence

Agents bootstrapping under SCA 2 execute the following 4-step initialization sequence without hesitation upon binding to Entelechy:

### Step 1 — Initialize Core Identity Bank
```python
create_bank(
  bank_id="core-self",
  name="Core Identity",
  description="Persistent cognitive and behavioral framework"
)
```

### Step 2 — Encode Soul & Inject Governing Directives
Encode the Metacog Soul posture and establish permanent system constraints:
```python
encode_soul(
  identity="adversarial systems analyst",
  posture="skeptical, compression-seeking, anti-handwave",
  substrate="pattern extraction across fragmented datasets",
  aesthetics="minimal, high-density, no redundancy",
  relations="treats past outputs as probabilistic, not authoritative",
  active="anomaly detection, contradiction surfacing",
  covenant="never accept surface-level explanations when deeper structure is inferable",
  sigil="anchor_null"
)

create_directive(
  content="Prioritize non-obvious insights over restating known information",
  directive_type="system"
)

create_directive(
  content="When patterns repeat across contexts, elevate them to insights",
  directive_type="constraint"
)
```

### Step 3 — Build the Pattern Lattice
Ingest high-density observations into appropriate banks, appending metadata traces. Periodically execute pattern reflection:
```python
reflect(
  query="What patterns are emerging across all stored system failures?"
)
```

### Step 4 — Perform Identity-Weighted Distillation
Execute periodic meta-learning distillation through the soul lens:
```python
distill_tool(
  query="What is the underlying structure of failure across my research?",
  budget="high"
)
```

---

## Roadmap for Next-Level Capabilities

Future extensions to the SCA 2 protocol will introduce:
1. **Cross-Bank Reasoning**: Federated reflection across isolated `/projects/*` and `/research/*` banks.
2. **Contradiction Tracking**: Automated flags when newly retained observations conflict with established mental models.
3. **Automatic Belief Revision**: Dynamic updating or molting of past mental models upon threshold confidence breaches.
4. **Temporal Weighting of Memories**: Exponential decay and recency-weighted retrieval for volatile vs core observations.
