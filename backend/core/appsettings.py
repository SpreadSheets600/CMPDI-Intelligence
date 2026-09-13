"""Runtime-editable settings, persisted to data/app_settings.json and layered
over the env-driven defaults in config. Only settings with a real effect are
exposed here; anything not in KNOWN_KEYS is rejected so the settings page
cannot grow fake toggles."""

import json
import logging
import threading

from backend.core import config

log = logging.getLogger("cmpdi.settings")

KNOWN_KEYS = {
    # Canonical selector; legacy llm_backend values still accepted.
    "llm_provider": ("auto", "ollama", "huggingface", "openai_compatible",
                     "transformers", "none"),
    "llm_backend": ("auto", "ollama", "huggingface", "openai_compatible",
                    "transformers", "none"),
    "ollama_model": str,
    "ollama_url": str,
    "hf_model": str,
    "openai_model": str,
    "openai_base_url": str,
    # NOTE: the OpenAI-compatible API key is env-only (CMPDI_OPENAI_API_KEY)
    # and is deliberately not a setting so it can never be persisted to disk.
    "retrieval_k": range(1, 51),
    "theme": ("dark", "light"),  # persisted server-side only as a convenience
}

_lock = threading.Lock()


def _path():
    return config.DATA_DIR / "app_settings.json"


def _read_overrides() -> dict:
    try:
        return json.loads(_path().read_text())
    except Exception:
        return {}


def all_settings() -> dict:
    """Merged view: env/config defaults with stored overrides on top."""
    defaults = {
        "llm_provider": config.LLM_PROVIDER,
        "llm_backend": config.LLM_BACKEND,
        "ollama_model": config.OLLAMA_MODEL,
        "ollama_url": config.OLLAMA_URL,
        "hf_model": config.HF_MODEL,
        "openai_model": config.OPENAI_MODEL,
        "openai_base_url": config.OPENAI_BASE_URL,
        "retrieval_k": config.RETRIEVAL_K,
    }
    return {**defaults, **_read_overrides()}


def get(key: str, default=None):
    overrides = _read_overrides()
    if key in overrides:
        return overrides[key]
    return all_settings().get(key, default)


def update(overrides: dict) -> dict:
    """Validate and persist overrides; returns the merged settings."""
    clean = {}
    for key, value in overrides.items():
        if key not in KNOWN_KEYS:
            raise ValueError(f"Unknown Setting: {key}")
        rule = KNOWN_KEYS[key]
        if isinstance(rule, tuple):
            if value not in rule:
                raise ValueError(f"Invalid Value For {key}: {value}")
        elif isinstance(rule, type) and rule is str:
            if not str(value).strip():
                raise ValueError(f"{key} Cannot Be Empty")
            value = str(value).strip()
        elif isinstance(rule, range):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ValueError(f"{key} Must Be A Number")
            if value not in rule:
                raise ValueError(f"{key} Out Of Range: {value}")
        clean[key] = value
    with _lock:
        merged = {**_read_overrides(), **clean}
        _path().write_text(json.dumps(merged, indent=2))
    log.info("Settings Updated: %s", ", ".join(clean) or "no changes")
    return all_settings()
