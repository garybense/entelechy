#!/usr/bin/env python3
"""
Quickstart examples for Entelechy API.
Run: python examples/api/quickstart.py
"""
import os
import requests

ENTELECHY_URL = os.getenv("ENTELECHY_API_URL", "http://localhost:8888")

# =============================================================================
# Doc Examples
# =============================================================================

# [docs:quickstart-full]
from entelechy_client import Entelechy

client = Entelechy(base_url="http://localhost:8888")

# Retain: Store information
client.retain(bank_id="my-bank", content="Alice works at Google as a software engineer")

# Recall: Search memories
client.recall(bank_id="my-bank", query="What does Alice do?")

# Reflect: Generate disposition-aware response
client.reflect(bank_id="my-bank", query="Tell me about Alice")
# [/docs:quickstart-full]


# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
requests.delete(f"{ENTELECHY_URL}/v1/default/banks/my-bank")

print("quickstart.py: All examples passed")
