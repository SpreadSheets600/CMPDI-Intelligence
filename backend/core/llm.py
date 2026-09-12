"""LLM backends: Ollama, raw Transformers, and extractive mode. Resolution
order follows the llm_backend setting; "auto" probes Ollama, then a locally
cached HF model, then extractive. Generation is optional: when no model
answers, the caller falls back to verbatim evidence snippets with citations."""

import json
import logging
import time
import urllib.request

from backend.core import appsettings, config

log = logging.getLogger("cmpdi.llm")

_transformers_model = None
_transformers_failed = False
_status_cache = None
_status_ts = 0.0


def _probe_ollama() -> bool:
    try:
        req = urllib.request.Request(f"{appsettings.get('ollama_url')}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=1.5):
            return True
    except Exception:
        return False


def _hf_model_cached(model_id: str) -> bool:
    try:
        from huggingface_hub import scan_cache_dir
        return any(r.repo_id == model_id for r in scan_cache_dir().repos)
    except Exception:
        return False


class OllamaBackend:
    name = "ollama"

    def __init__(self):
        self.model = appsettings.get("ollama_model")

    def generate(self, system: str, user: str) -> str | None:
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": 0.1},
        }).encode()
        req = urllib.request.Request(
            f"{appsettings.get('ollama_url')}/api/chat", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
                return data["message"]["content"]
        except Exception as e:
            log.warning("Ollama Generation Failed, Falling Back: %s", e)
            return None


class TransformersBackend:
    name = "transformers"

    def generate(self, system: str, user: str) -> str | None:
        global _transformers_model, _transformers_failed
        if _transformers_failed:
            return None
        try:
            if _transformers_model is None:
                from transformers import pipeline
                _transformers_model = pipeline(
                    "text-generation", model=config.LLM_MODEL,
                    torch_dtype="auto", device_map="cpu")
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": user}]
            out = _transformers_model(messages, max_new_tokens=512, temperature=0.1)
            return out[0]["generated_text"][-1]["content"]
        except Exception as e:
            log.warning("Transformers Generation Failed, Falling Back: %s", e)
            _transformers_failed = True
            return None


class ExtractiveBackend:
    name = "extractive"

    def generate(self, system: str, user: str) -> str | None:
        return None


def get_backend():
    mode = appsettings.get("llm_backend")
    if mode == "none":
        return ExtractiveBackend()
    if mode == "ollama" or (mode == "auto" and _probe_ollama()):
        return OllamaBackend()
    if mode == "transformers" or (mode == "auto" and _hf_model_cached(config.LLM_MODEL)):
        return TransformersBackend()
    return ExtractiveBackend()


def status() -> dict:
    """Dashboard/settings probe of the active backend, cached for 60s so page
    loads never block on Ollama timeouts."""
    global _status_cache, _status_ts
    if _status_cache and time.time() - _status_ts < 60:
        return _status_cache
    mode = appsettings.get("llm_backend")
    info = {"configured": mode, "model": None, "available": False, "detail": ""}
    if mode == "none":
        info["detail"] = "Generation disabled; answers use verbatim evidence."
    elif mode == "ollama" or (mode == "auto" and _probe_ollama()):
        backend = OllamaBackend()
        info.update(model=backend.model, available=True, backend="ollama")
        try:
            req = urllib.request.Request(f"{appsettings.get('ollama_url')}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as resp:
                models = [m["name"] for m in json.loads(resp.read()).get("models", [])]
            info["detail"] = f"{len(models)} model(s) installed"
        except Exception as e:
            info["detail"] = f"probe failed: {e}"
    elif mode == "transformers" or (mode == "auto" and _hf_model_cached(config.LLM_MODEL)):
        info.update(backend="transformers", model=config.LLM_MODEL, available=True,
                    detail="locally cached HF model")
    else:
        info["backend"] = "extractive"
        info["detail"] = "No generation backend reachable; evidence-only answers."
    _status_cache, _status_ts = info, time.time()
    return info


def reset_status_cache():
    global _status_cache
    _status_cache = None
