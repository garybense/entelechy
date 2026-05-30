# Entelechy Pipecat Integration

Persistent long-term memory for [Pipecat](https://github.com/pipecat-ai/pipecat) voice AI pipelines via [Entelechy](https://vectorize.io/entelechy). A single `FrameProcessor` slots between your user context aggregator and LLM service — recalling relevant memories before each turn and retaining conversation content after.

## Quick Start

```bash
pip install entelechy-pipecat
```

```python
from pipecat.pipeline.pipeline import Pipeline
from entelechy_pipecat import EntelechyMemoryService

memory = EntelechyMemoryService(
    bank_id="user-123",
    entelechy_api_url="http://localhost:8888",
)

pipeline = Pipeline([
    transport.input(),
    stt_service,
    user_aggregator,
    memory,           # ← add between user_aggregator and LLM
    llm_service,
    assistant_aggregator,
    tts_service,
    transport.output(),
])
```

Or with [Entelechy Cloud](https://ui.mindmods.org/signup):

```python
memory = EntelechyMemoryService(
    bank_id="user-123",
    entelechy_api_url="https://api.mindmods.org",
    api_key="hsk_your_token_here",
)
```

## How It Works

```
New turn starts
  └─ OpenAILLMContextFrame arrives
       ├─ Retain previous complete turn (user+assistant) — fire-and-forget
       └─ Recall relevant memories for current user query
            └─ Inject as <entelechy_memories> system message
                 └─ Forward enriched context to LLM
```

On each `OpenAILLMContextFrame`:

1. **Retain** — any new complete user+assistant turn pairs are sent to Entelechy asynchronously (non-blocking)
2. **Recall** — the latest user message is used as the search query; results are injected as a system message before the LLM sees the context
3. **Forward** — the enriched context frame is pushed downstream

Memory accumulates across calls. By the third or fourth turn, recall starts surfacing useful context that the pipeline didn't have to re-establish.

## Prerequisites

A running Entelechy instance:

**Self-hosted:**
```bash
pip install entelechy-all
export ENTELECHY_API_LLM_API_KEY=your-api-key
entelechy-api  # starts on http://localhost:8888
```

**Entelechy Cloud:** [Sign up](https://ui.mindmods.org/signup) — no self-hosting required.

## Configuration

```python
EntelechyMemoryService(
    bank_id="user-123",               # Required: memory bank to use
    entelechy_api_url="...",          # Entelechy API URL
    api_key="hsk_...",                # API key (Entelechy Cloud)
    recall_budget="mid",              # "low", "mid", or "high"
    recall_max_tokens=4096,           # Max tokens for recall results
    enable_recall=True,               # Inject memories before LLM
    enable_retain=True,               # Store turns after each exchange
    memory_prefix="Relevant memories from past conversations:\n",
)
```

### Global configuration

```python
from entelechy_pipecat import configure

configure(
    entelechy_api_url="http://localhost:8888",
    api_key="hsk_...",
    recall_budget="mid",
)

# Now create services without repeating connection details
memory = EntelechyMemoryService(bank_id="user-123")
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```
