"""Configuration management for Entelechy Codex plugin.

Loads settings from settings.json (plugin defaults) merged with environment
variable overrides. Full config schema matching Openclaw's 30+ options.
"""

import json
import os
import sys

DEFAULTS = {
    # Recall
    "autoRecall": True,
    "recallBudget": "mid",
    "recallMaxTokens": 1024,
    "recallTypes": ["world", "experience"],
    "recallContextTurns": 1,
    "recallMaxQueryChars": 800,
    "recallRoles": ["user", "assistant"],
    "recallPromptPreamble": (
        "Relevant memories from past conversations (prioritize recent when "
        "conflicting). Only use memories that are directly useful to continue "
        "this conversation; ignore the rest:"
    ),
    # Retain
    "autoRetain": True,
    "retainMode": "full-session",
    "retainRoles": ["user", "assistant"],
    "retainEveryNTurns": 10,
    "retainOverlapTurns": 2,
    "retainContext": "codex",
    "retainTags": [],
    "retainMetadata": {},
    # Connection
    "entelechyApiUrl": None,
    "entelechyApiToken": None,
    "apiPort": 9077,
    "daemonIdleTimeout": 0,
    "embedVersion": "latest",
    "embedPackagePath": None,
    # Bank
    "bankId": None,
    "bankIdPrefix": "",
    "dynamicBankId": False,
    "dynamicBankGranularity": ["agent", "project"],
    "bankMission": "",
    "retainMission": None,
    "agentName": "codex",
    # LLM (for daemon mode)
    "llmProvider": None,
    "llmModel": None,
    "llmApiKeyEnv": None,
    # Misc
    "debug": False,
}

# Map env var names to config keys and their types
ENV_OVERRIDES = {
    "ENTELECHY_API_URL": ("entelechyApiUrl", str),
    "ENTELECHY_API_TOKEN": ("entelechyApiToken", str),
    "ENTELECHY_BANK_ID": ("bankId", str),
    "ENTELECHY_AGENT_NAME": ("agentName", str),
    "ENTELECHY_AUTO_RECALL": ("autoRecall", bool),
    "ENTELECHY_AUTO_RETAIN": ("autoRetain", bool),
    "ENTELECHY_RETAIN_MODE": ("retainMode", str),
    "ENTELECHY_RECALL_BUDGET": ("recallBudget", str),
    "ENTELECHY_RECALL_MAX_TOKENS": ("recallMaxTokens", int),
    "ENTELECHY_RECALL_MAX_QUERY_CHARS": ("recallMaxQueryChars", int),
    "ENTELECHY_RECALL_CONTEXT_TURNS": ("recallContextTurns", int),
    "ENTELECHY_API_PORT": ("apiPort", int),
    "ENTELECHY_DAEMON_IDLE_TIMEOUT": ("daemonIdleTimeout", int),
    "ENTELECHY_EMBED_VERSION": ("embedVersion", str),
    "ENTELECHY_EMBED_PACKAGE_PATH": ("embedPackagePath", str),
    "ENTELECHY_DYNAMIC_BANK_ID": ("dynamicBankId", bool),
    "ENTELECHY_BANK_MISSION": ("bankMission", str),
    "ENTELECHY_LLM_PROVIDER": ("llmProvider", str),
    "ENTELECHY_LLM_MODEL": ("llmModel", str),
    "ENTELECHY_DEBUG": ("debug", bool),
}


def _cast_env(value: str, typ):
    """Cast environment variable string to target type. Returns None on failure."""
    try:
        if typ is bool:
            return value.lower() in ("true", "1", "yes")
        if typ is int:
            return int(value)
        return value
    except (ValueError, AttributeError):
        return None


def _load_settings_file(path: str, config: dict) -> None:
    """Merge a settings.json file into config in-place. Silently skips if missing."""
    if not os.path.exists(path):
        return
    try:
        with open(path) as f:
            file_config = json.load(f)
        config.update({k: v for k, v in file_config.items() if v is not None})
    except (json.JSONDecodeError, OSError) as e:
        debug_log(config, f"Failed to load {path}: {e}")


def load_config() -> dict:
    """Load plugin configuration from settings.json + env overrides.

    Loading order (later entries win):
      1. Built-in defaults
      2. Plugin install settings.json  (~/.entelechy/codex/settings.json)
      3. User config                   (~/.entelechy/codex.json)
      4. Environment variable overrides

    ~/.entelechy/codex.json is the recommended place to configure the
    plugin — stable across updates.
    """
    config = dict(DEFAULTS)

    # 1. Plugin install settings.json (written by get-codex installer)
    install_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _load_settings_file(os.path.join(install_root, "settings.json"), config)

    # 2. User config — stable, version-independent
    user_config_path = os.path.join(os.path.expanduser("~"), ".entelechy", "codex.json")
    _load_settings_file(user_config_path, config)

    # Apply environment variable overrides
    for env_name, (key, typ) in ENV_OVERRIDES.items():
        val = os.environ.get(env_name)
        if val is not None:
            cast_val = _cast_env(val, typ)
            if cast_val is not None:
                config[key] = cast_val

    return config


def debug_log(config: dict, *args):
    """Log to stderr if debug mode is enabled."""
    if config.get("debug"):
        print("[Entelechy]", *args, file=sys.stderr)
