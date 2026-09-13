"""LLM façade. Application code imports from here — never from providers
directly and never from a concrete backend:

    from backend.core.llm import get_backend, get_provider

``get_backend()`` preserves the historic interface (``.generate``,
``.name``); ``get_provider()`` exposes the full unified interface
(``complete`` / ``complete_json`` / ``describe_image`` / ``validate`` /
``health_check`` plus capability flags).
"""

import time

from backend.core.llm.providers import (
    ExtractiveProvider,
    HuggingFaceProvider,
    LLMError,
    LLMProvider,
    LLMResponse,
    OllamaProvider,
    OpenAICompatProvider,
    get_provider,
    reset_provider_cache,
    safe_status,
    selected_id,
)

# Backward-compatible aliases (vision.py used OllamaBackend directly)
OllamaBackend = OllamaProvider
TransformersBackend = HuggingFaceProvider
ExtractiveBackend = ExtractiveProvider

_status_cache = None
_status_ts = 0.0


class _BackendShim:
    """Historic duck-type: .name + .generate(system, user). All new code
    should use get_provider() instead."""

    def __init__(self, provider: LLMProvider):
        self._p = provider
        self.name = ("extractive" if not provider.generative
                     else provider.provider_id)
        # legacy names some call sites may compare against
        if provider.provider_id == "huggingface":
            self.legacy_name = "transformers"
        else:
            self.legacy_name = self.name

    def generate(self, system: str, user: str) -> str | None:
        return self._p.generate(system, user)

    @property
    def provider(self) -> LLMProvider:
        return self._p


def get_backend() -> _BackendShim:
    return _BackendShim(get_provider())


def status() -> dict:
    """Dashboard/settings probe, cached for 60s so page loads never block
    on backend timeouts. Safe fields only."""
    global _status_cache, _status_ts
    if _status_cache and time.time() - _status_ts < 60:
        return _status_cache
    _status_cache, _status_ts = safe_status(), time.time()
    return _status_cache


def reset_status_cache():
    global _status_cache
    _status_cache = None


__all__ = [
    "LLMError", "LLMResponse", "LLMProvider",
    "OllamaProvider", "OllamaBackend",
    "HuggingFaceProvider", "TransformersBackend",
    "OpenAICompatProvider", "ExtractiveProvider", "ExtractiveBackend",
    "get_provider", "get_backend", "reset_provider_cache",
    "reset_status_cache", "safe_status", "selected_id", "status",
]
