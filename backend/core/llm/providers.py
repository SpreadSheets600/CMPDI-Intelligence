"""Unified generative-inference providers. Exactly three execution modes —
local Hugging Face, local Ollama, OpenAI-compatible API — behind one
interface, plus the extractive no-generation fallback that keeps the
local-first pipeline usable when no inference backend is available.

Application code must only use ``get_provider()`` / ``get_backend()`` and
the ``generate`` / ``complete`` / ``complete_json`` / ``describe_image``
methods. No provider-specific logic belongs outside this module.

Embeddings, OCR, parsing, storage and retrieval are intentionally NOT part
of this layer; they stay local (see core/pipeline/embedder.py).
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

log = logging.getLogger("cmpdi.llm")

# --------------------------------------------------------------------------
# Common response representation. Provider adapters normalize everything
# into this; provider-specific objects must never leak to callers.


@dataclass
class LLMError:
    kind: str    # config|connection|auth|model_not_found|rate_limit|timeout
                 # |bad_response|server|generation|unsupported
    message: str


@dataclass
class LLMResponse:
    ok: bool
    text: str = ""
    structured: dict | None = None
    provider: str = ""
    model: str = ""
    latency_s: float = 0.0
    finish_reason: str = ""          # stop|length|error|unavailable|...
    usage: dict | None = None        # {prompt_tokens, completion_tokens, ...}
    error: LLMError | None = None

    @property
    def failed(self) -> bool:
        return not self.ok


# --------------------------------------------------------------------------
# Provider base


class LLMProvider:
    """One interface for all generative backends.

    Capabilities are explicit so callers (and the future report generator)
    can adapt without provider sniffing: ``generative`` (False = extractive
    fallback), ``supports_vision``, ``supports_structured`` ("native" means
    server-enforced JSON, "prompt" means constrained prompting + parsing,
    None means unsupported).
    """

    provider_id = "base"

    def __init__(self, model: str):
        self.model = model

    @property
    def generative(self) -> bool:
        return True

    @property
    def supports_vision(self) -> bool:
        return False

    @property
    def supports_structured(self) -> str | None:
        return None

    # -- core operations -------------------------------------------------

    def complete(self, messages: list[dict], max_tokens: int = 512,
                 temperature: float = 0.1,
                 json_mode: bool = False) -> LLMResponse:
        raise NotImplementedError

    def generate(self, system: str, user: str) -> str | None:
        """Backward-compatible text API used by retrieval/summarization/
        agent code. Returns the text or None when unavailable."""
        resp = self.complete(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}])
        return resp.text if resp.ok and resp.text else None

    def complete_json(self, system: str, user: str,
                      max_tokens: int = 512) -> tuple[dict | None, LLMResponse]:
        """Structured generation. Strategy differences (native JSON mode vs
        constrained prompting) live inside the adapters; callers get a
        dict or (None + error response) either way."""
        resp = self.complete(
            [{"role": "system", "content": system + "\nReply with JSON only."},
             {"role": "user", "content": user}],
            max_tokens=max_tokens, temperature=0.0, json_mode=True)
        if not resp.ok:
            return None, resp
        parsed = _parse_json_text(resp.text)
        if parsed is None:
            resp.ok = False
            resp.finish_reason = "bad_response"
            resp.error = LLMError("bad_response",
                                  "Backend returned non-JSON output")
            return None, resp
        resp.structured = parsed
        return parsed, resp

    def describe_image(self, png_bytes: bytes, prompt: str,
                       caption: str = "") -> LLMResponse:
        return LLMResponse(ok=False, provider=self.provider_id,
                           model=self.model, finish_reason="unsupported",
                           error=LLMError("unsupported",
                                          f"{self.provider_id} cannot take images"))

    # -- health ------------------------------------------------------------

    def validate(self) -> list[str]:
        """Static configuration problems. Empty = configured."""
        return []

    def health_check(self) -> dict:
        """Cheap live probe: minimal deterministic inference. Safe to
        expose (no prompts, no secrets in output)."""
        errs = self.validate()
        out: dict = {"provider": self.provider_id, "model": self.model,
                     "generative": self.generative,
                     "vision": self.supports_vision,
                     "structured": self.supports_structured,
                     "config_valid": not errs, "config_errors": errs,
                     "reachable": False, "model_available": False,
                     "inference_ok": False, "latency_s": None,
                     "failure": None}
        if errs:
            out["failure"] = "; ".join(errs)
            return out
        t0 = time.perf_counter()
        try:
            resp = self.complete(
                [{"role": "user", "content": "Reply with exactly: OK"}],
                max_tokens=8, temperature=0.0)
        except Exception as e:  # adapters classify; this is a last resort
            out["failure"] = f"{type(e).__name__}: {e}"
            return out
        out["latency_s"] = round(time.perf_counter() - t0, 2)
        out["reachable"] = True
        if resp.ok and resp.text.strip().upper().startswith("OK"):
            out["model_available"] = True
            out["inference_ok"] = True
        else:
            out["model_available"] = resp.error is None or \
                resp.error.kind not in ("model_not_found", "connection",
                                        "timeout", "auth", "config")
            out["failure"] = resp.error.message if resp.error else \
                f"unexpected reply: {resp.text[:80]!r}"
        return out

    # -- observability: safe metadata only, never prompts or secrets --------

    def _log(self, resp: LLMResponse, op: str):
        log.info("LLM %s provider=%s model=%s ok=%s latency=%.2fs %s",
                 op, resp.provider, resp.model, resp.ok, resp.latency_s,
                 (resp.error.kind if resp.error else resp.finish_reason))


def _parse_json_text(content: str) -> dict | None:
    s = (content or "").strip()
    if s.startswith("```"):
        s = s.strip("`").strip()
        if s.lower().startswith("json"):
            s = s[4:].strip()
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    start, end = s.find("{"), s.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(s[start:end + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def _http_json(url: str, payload: dict | None, timeout: float,
               headers: dict | None = None,
               method: str | None = None) -> tuple[int | None, dict | str]:
    """POST (or GET when payload is None) JSON helper that maps transport
    failures to (None, kind-string) instead of raising."""
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method=method or ("POST" if data else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read() or b"{}")
        except Exception:
            body = {"error": f"HTTP {e.code}"}
        return e.code, body
    except TimeoutError:
        return None, "__timeout__"
    except (ConnectionError, OSError) as e:
        # urllib raises URLError (an OSError) for refused/unreachable hosts
        msg = str(e)
        if "timed out" in msg:
            return None, "__timeout__"
        return None, "__connection__"
    except Exception as e:
        return None, f"__error__: {e}"


# --------------------------------------------------------------------------
# Ollama (local server, configurable model + host)


class OllamaProvider(LLMProvider):
    provider_id = "ollama"

    def __init__(self, model: str, base_url: str, timeout: float = 180.0):
        super().__init__(model)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def supports_vision(self) -> bool:
        return True  # attempted; model may refuse -> vision_skipped

    @property
    def supports_structured(self) -> str:
        return "native"  # format: "json"

    def _server_up(self) -> bool:
        status, _ = _http_json(f"{self.base_url}/api/tags", None, 5.0)
        return status == 200

    def _model_present(self) -> bool | None:
        """True/False when the server answers, None when unreachable."""
        status, body = _http_json(f"{self.base_url}/api/tags", None, 5.0)
        if status != 200 or not isinstance(body, dict):
            return None
        names = set()
        for m in body.get("models", []) or []:
            for key in ("name", "model"):
                if m.get(key):
                    names.add(str(m[key]).split(":")[0])
                    names.add(str(m[key]))
        want = (self.model or "").split(":")[0]
        return want in names or self.model in names

    def validate(self) -> list[str]:
        errs = []
        if not self.base_url:
            errs.append("Ollama URL is empty (CMPDI_OLLAMA_URL)")
        if not self.model:
            errs.append("Ollama model is empty (CMPDI_OLLAMA_MODEL)")
        return errs

    def complete(self, messages, max_tokens=512, temperature=0.1,
                 json_mode=False) -> LLMResponse:
        t0 = time.perf_counter()
        payload: dict = {"model": self.model, "messages": messages,
                         "stream": False,
                         "options": {"temperature": temperature,
                                     "num_predict": max_tokens}}
        if json_mode:
            payload["format"] = "json"
        status, body = _http_json(f"{self.base_url}/api/chat", payload,
                                  self.timeout)
        dt = time.perf_counter() - t0
        if body == "__timeout__":
            return self._err("timeout", "Ollama request timed out", dt)
        if body == "__connection__":
            return self._err("connection",
                             f"Ollama server not reachable at {self.base_url}", dt)
        if isinstance(body, str):
            return self._err("generation", body, dt)
        if status != 200:
            msg = (body.get("error") if isinstance(body, dict) else "") or \
                f"HTTP {status}"
            kind = "model_not_found" if status == 404 and "model" in str(msg).lower() \
                else ("server" if (status or 0) >= 500 else "generation")
            return self._err(kind, f"Ollama error: {msg}", dt)
        try:
            content = body["message"]["content"]
        except (KeyError, TypeError):
            return self._err("bad_response",
                             "Ollama returned a malformed response", dt)
        usage = None
        if isinstance(body, dict) and ("eval_count" in body or
                                       "prompt_eval_count" in body):
            usage = {"completion_tokens": body.get("eval_count"),
                     "prompt_tokens": body.get("prompt_eval_count")}
        resp = LLMResponse(ok=True, text=content or "", provider="ollama",
                           model=self.model, latency_s=round(dt, 2),
                           finish_reason=body.get("done_reason") or "stop",
                           usage=usage)
        self._log(resp, "complete")
        return resp

    def describe_image(self, png_bytes: bytes, prompt: str,
                       caption: str = "") -> LLMResponse:
        import base64
        t0 = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": [{"role": "user",
                          "content": (f"Caption: {caption}\n" if caption else "")
                          + prompt,
                          "images": [base64.b64encode(png_bytes).decode()]}],
            "stream": False, "options": {"temperature": 0.1}}
        status, body = _http_json(f"{self.base_url}/api/chat", payload,
                                  self.timeout)
        dt = time.perf_counter() - t0
        if body in ("__timeout__", "__connection__") or isinstance(body, str):
            return self._err("connection" if body != "__timeout__"
                             else "timeout", "vision request failed", dt)
        if status != 200:
            msg = (body.get("error") if isinstance(body, dict) else "") or \
                f"HTTP {status}"
            low = str(msg).lower()
            if "image" in low or "vision" in low or "multimodal" in low \
                    or status == 404:
                return self._err("unsupported",
                                 f"model {self.model} refused images: {msg}", dt)
            return self._err("generation", f"Ollama error: {msg}", dt)
        try:
            content = body["message"]["content"]
        except (KeyError, TypeError):
            return self._err("bad_response", "malformed vision response", dt)
        resp = LLMResponse(ok=True, text=content or "", provider="ollama",
                           model=self.model, latency_s=round(dt, 2),
                           finish_reason="stop")
        self._log(resp, "vision")
        return resp

    def health_check(self) -> dict:
        out = super().health_check()
        present = self._model_present()
        out["reachable"] = present is not None
        if present is False:
            out["model_available"] = False
            out["inference_ok"] = False
            out["failure"] = (f"model '{self.model}' not found on "
                              f"{self.base_url} (pull it with "
                              f"`ollama pull {self.model}`)")
        elif present is True:
            out["model_available"] = out["model_available"] or \
                out["inference_ok"]
        return out

    def _err(self, kind, message, dt) -> LLMResponse:
        resp = LLMResponse(ok=False, provider="ollama", model=self.model,
                           latency_s=round(dt, 2), finish_reason="error",
                           error=LLMError(kind, message))
        self._log(resp, "complete")
        return resp


# --------------------------------------------------------------------------
# Hugging Face local inference (already-downloaded models only)


_hf_lock = threading.Lock()
_hf_loaded: dict = {}   # resolved_path -> pipeline (one model at a time ideally)


class HuggingFaceProvider(LLMProvider):
    provider_id = "huggingface"

    def __init__(self, model: str):
        super().__init__(model)

    @property
    def supports_structured(self) -> str:
        return "prompt"  # constrained prompting + strict parsing

    def resolve_local(self) -> tuple[str | None, str]:
        """Resolve to a local snapshot path WITHOUT downloading.
        Returns (path, error_message)."""
        from pathlib import Path
        ident = (self.model or "").strip()
        if not ident:
            return None, ("Hugging Face model is empty "
                          "(CMPDI_HF_MODEL or CMPDI_LLM_MODEL)")
        p = Path(ident).expanduser()
        if p.is_dir():
            if not ((p / "config.json").exists()):
                return None, (f"Local model directory {p} has no config.json")
            tok = (p / "tokenizer.json").exists() or \
                (p / "tokenizer_config.json").exists()
            if not tok:
                return None, (f"{p} has no tokenizer files")
            return str(p), ""
        try:
            from huggingface_hub import snapshot_download
            path = snapshot_download(repo_id=ident, local_files_only=True)
            return path, ""
        except Exception:
            return None, (
                f"Model '{ident}' is not available locally and downloads are "
                f"disabled. Pre-download it (e.g. `huggingface-cli download "
                f"{ident}`) or set CMPDI_HF_MODEL to a local directory.")

    def validate(self) -> list[str]:
        _, err = self.resolve_local()
        return [err] if err else []

    def _load(self):
        path, err = self.resolve_local()
        if err:
            raise RuntimeError(err)
        with _hf_lock:
            if path not in _hf_loaded:
                from transformers import pipeline
                try:
                    _hf_loaded[path] = pipeline(
                        "text-generation", model=path,
                        torch_dtype="auto", device_map="cpu",
                        trust_remote_code=False)
                except Exception as e:
                    raise RuntimeError(
                        f"Could not load '{self.model}': "
                        f"{type(e).__name__}: {e}. The architecture may be "
                        f"unsupported or the machine may lack memory.") from e
            return _hf_loaded[path]

    def complete(self, messages, max_tokens=512, temperature=0.1,
                 json_mode=False) -> LLMResponse:
        t0 = time.perf_counter()

        def fail(kind, message):
            resp = LLMResponse(ok=False, provider="huggingface",
                               model=self.model,
                               latency_s=round(time.perf_counter() - t0, 2),
                               finish_reason="error",
                               error=LLMError(kind, message))
            self._log(resp, "complete")
            return resp

        try:
            pipe = self._load()
        except RuntimeError as e:
            msg = str(e)
            kind = "config" if "not available locally" in msg or \
                "empty" in msg else "generation"
            return fail(kind, msg)
        try:
            out = pipe(messages, max_new_tokens=max_tokens,
                       do_sample=False, return_full_text=False)
            text = out[0]["generated_text"]
            if isinstance(text, list):  # chat template path
                text = text[-1].get("content", "") if text else ""
            text = text if isinstance(text, str) else str(text)
        except Exception as e:
            # fall back to a plain prompt string for non-chat pipelines
            try:
                prompt = "\n".join(
                    f"{m.get('role', 'user')}: {m.get('content', '')}"
                    for m in messages) + "\nassistant:"
                out = pipe(prompt, max_new_tokens=max_tokens,
                           do_sample=False)
                text = out[0]["generated_text"]
                text = text[len(prompt):] if text.startswith(prompt) else text
            except Exception as e2:
                return fail("generation",
                            f"{type(e2).__name__}: {e2}")
        resp = LLMResponse(ok=True, text=(text or "").strip(),
                           provider="huggingface", model=self.model,
                           latency_s=round(time.perf_counter() - t0, 2),
                           finish_reason="stop", usage=None)
        self._log(resp, "complete")
        return resp


# --------------------------------------------------------------------------
# OpenAI-compatible API (any server speaking /chat/completions)


class OpenAICompatProvider(LLMProvider):
    provider_id = "openai_compatible"

    def __init__(self, model: str, base_url: str, api_key: str = "",
                 timeout: float = 60.0):
        super().__init__(model)
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.timeout = timeout

    @property
    def supports_structured(self) -> str:
        return "native"  # response_format json_object, with prompt fallback

    @property
    def endpoint_host(self) -> str:
        try:
            return self.base_url.split("://", 1)[1].split("/", 1)[0]
        except Exception:
            return ""

    def validate(self) -> list[str]:
        errs = []
        if not self.base_url:
            errs.append("OpenAI-compatible base URL is empty "
                        "(CMPDI_OPENAI_BASE_URL)")
        elif not (self.base_url.startswith("http://")
                  or self.base_url.startswith("https://")):
            errs.append(f"Base URL must start with http(s)://: {self.base_url}")
        if not self.model:
            errs.append("OpenAI-compatible model is empty (CMPDI_OPENAI_MODEL)")
        return errs

    def _headers(self) -> dict:
        h = {}
        if self.api_key:
            h["Authorization"] = "Bearer ***"  # never the real key in logs;
            # the real header is attached at send time below
        return h

    def complete(self, messages, max_tokens=512, temperature=0.1,
                 json_mode=False) -> LLMResponse:
        t0 = time.perf_counter()

        def fail(kind, message):
            resp = LLMResponse(ok=False, provider="openai_compatible",
                               model=self.model,
                               latency_s=round(time.perf_counter() - t0, 2),
                               finish_reason="error",
                               error=LLMError(kind, message))
            self._log(resp, "complete")
            return resp

        if self.validate():
            return fail("config", "; ".join(self.validate()))
        # single attempt by design: no aggressive retries against paid APIs
        for attempt_json in ([True, False] if json_mode else [False]):
            payload = {"model": self.model, "messages": messages,
                       "temperature": temperature, "max_tokens": max_tokens}
            if attempt_json:
                payload["response_format"] = {"type": "json_object"}
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions", data=data,
                headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req,
                                            timeout=self.timeout) as resp:
                    body = json.loads(resp.read() or b"{}")
            except urllib.error.HTTPError as e:
                try:
                    body = json.loads(e.read() or b"{}")
                except Exception:
                    body = {}
                msg = ((body.get("error") or {}).get("message")
                       if isinstance(body, dict) else "") or f"HTTP {e.code}"
                if e.code == 401:
                    return fail("auth",
                                f"Authentication failed for {self.endpoint_host}: "
                                f"{msg}. Check CMPDI_OPENAI_API_KEY.")
                if e.code == 404:
                    return fail("model_not_found",
                                f"Model '{self.model}' not found at "
                                f"{self.endpoint_host}: {msg}")
                if e.code == 429:
                    return fail("rate_limit", f"Rate limited: {msg}")
                if e.code >= 500:
                    return fail("server",
                                f"Server error at {self.endpoint_host}: {msg}")
                return fail("generation", f"Request failed: {msg}")
            except TimeoutError:
                return fail("timeout",
                            f"Request to {self.endpoint_host} timed out "
                            f"after {self.timeout}s")
            except (ConnectionError, OSError) as e:
                if "timed out" in str(e):
                    return fail("timeout",
                                f"Request to {self.endpoint_host} timed out")
                return fail("connection",
                            f"Cannot reach {self.endpoint_host}: "
                            f"{type(e).__name__}")
            except Exception as e:
                return fail("generation", f"{type(e).__name__}: {e}")
            try:
                choice = body["choices"][0]
                content = (choice.get("message") or {}).get("content") or ""
            except (KeyError, IndexError, TypeError):
                if attempt_json:
                    continue  # server ignored response_format; retry plain
                return fail("bad_response",
                            "Endpoint returned a malformed response")
            if attempt_json and _parse_json_text(content) is None:
                continue  # native mode unsupported; fall back to prompting
            resp = LLMResponse(
                ok=True, text=content, provider="openai_compatible",
                model=self.model, latency_s=round(time.perf_counter() - t0, 2),
                finish_reason=choice.get("finish_reason") or "stop",
                usage=body.get("usage") if isinstance(body, dict) else None)
            self._log(resp, "complete")
            return resp
        return fail("bad_response",
                    "Endpoint did not return parseable JSON output")

    def health_check(self) -> dict:
        out = super().health_check()
        out["endpoint"] = self.endpoint_host
        out["auth_configured"] = bool(self.api_key)
        return out


# --------------------------------------------------------------------------
# Extractive fallback: no generation; local pipeline keeps working


class ExtractiveProvider(LLMProvider):
    provider_id = "extractive"

    def __init__(self):
        super().__init__("extractive")

    @property
    def generative(self) -> bool:
        return False

    def complete(self, messages, max_tokens=512, temperature=0.1,
                 json_mode=False) -> LLMResponse:
        return LLMResponse(ok=False, provider="extractive", model="extractive",
                           finish_reason="unavailable",
                           error=LLMError("unavailable",
                                          "No generative backend configured; "
                                          "evidence-only mode"))

    def health_check(self) -> dict:
        return {"provider": "extractive", "model": "extractive",
                "generative": False, "vision": False, "structured": None,
                "config_valid": True, "config_errors": [],
                "reachable": True, "model_available": True,
                "inference_ok": False,
                "latency_s": 0.0,
                "failure": "extractive mode: retrieval works, no generation"}


# --------------------------------------------------------------------------
# Central selection + observability-safe status


_instances: dict = {}
_instances_lock = threading.Lock()

# legacy llm_backend values -> canonical provider ids
_ALIASES = {"transformers": "huggingface", "hf": "huggingface",
            "openai": "openai_compatible",
            "openai-compatible": "openai_compatible"}


def selected_id() -> str:
    """Configured provider id after alias resolution ('auto'/'none' are
    resolution modes, not providers)."""
    from backend.core import appsettings
    raw = str(appsettings.get("llm_provider")
              or appsettings.get("llm_backend") or "auto").strip().lower()
    return _ALIASES.get(raw, raw)


def _build(provider_id: str) -> LLMProvider:
    from backend.core import appsettings, config
    if provider_id == "ollama":
        return OllamaProvider(
            model=appsettings.get("ollama_model") or config.OLLAMA_MODEL,
            base_url=appsettings.get("ollama_url") or config.OLLAMA_URL,
            timeout=float(getattr(config, "OLLAMA_TIMEOUT", 180.0)))
    if provider_id == "huggingface":
        return HuggingFaceProvider(
            model=appsettings.get("hf_model") or config.HF_MODEL)
    if provider_id == "openai_compatible":
        return OpenAICompatProvider(
            model=appsettings.get("openai_model") or config.OPENAI_MODEL,
            base_url=appsettings.get("openai_base_url")
            or config.OPENAI_BASE_URL,
            api_key=config.OPENAI_API_KEY,  # env only, never persisted
            timeout=float(getattr(config, "OPENAI_TIMEOUT", 60.0)))
    return ExtractiveProvider()


def _ollama_reachable() -> bool:
    from backend.core import appsettings, config
    url = (appsettings.get("ollama_url") or config.OLLAMA_URL or "").rstrip("/")
    if not url:
        return False
    status, _ = _http_json(f"{url}/api/tags", None, 2.0)
    return status == 200


def _hf_resolvable() -> bool:
    from backend.core import appsettings, config
    ident = (appsettings.get("hf_model") or config.HF_MODEL or "").strip()
    if not ident:
        return False
    return HuggingFaceProvider(ident).validate() == []


def _openai_configured() -> bool:
    from backend.core import appsettings, config
    url = (appsettings.get("openai_base_url") or config.OPENAI_BASE_URL
           or "").strip()
    model = (appsettings.get("openai_model") or config.OPENAI_MODEL
             or "").strip()
    return bool(url and model)


def get_provider(provider_id: str | None = None) -> LLMProvider:
    """Central selection. Explicit id, else configured mode: 'auto' probes
    ollama -> openai-compatible (if configured) -> huggingface (if cached)
    -> extractive; 'none' forces extractive. Instances are cached per
    (provider, model) so local HF models load once."""
    pid = (provider_id or selected_id()).strip().lower()
    pid = _ALIASES.get(pid, pid)
    if pid == "none":
        pid = "extractive"
    elif pid == "auto":
        if _ollama_reachable():
            pid = "ollama"
        elif _openai_configured():
            pid = "openai_compatible"
        elif _hf_resolvable():
            pid = "huggingface"
        else:
            pid = "extractive"
    if pid not in ("ollama", "huggingface", "openai_compatible"):
        pid = "extractive"
    provider = _build(pid)
    key = (pid, provider.model,
           getattr(provider, "base_url", ""))
    with _instances_lock:
        if key not in _instances:
            _instances[key] = provider
        return _instances[key]


def reset_provider_cache():
    with _instances_lock:
        _instances.clear()
    from backend.core.llm import reset_status_cache as _r
    _r()


def safe_status(provider: LLMProvider | None = None) -> dict:
    """Dashboard-safe status: provider, model, endpoint host, capabilities,
    validation — never keys, tokens, or prompts."""
    p = provider or get_provider()
    info: dict = {"provider": p.provider_id, "model": p.model,
                  "generative": p.generative, "available": p.generative,
                  "vision": p.supports_vision,
                  "structured": p.supports_structured,
                  "config_errors": p.validate()}
    if isinstance(p, OllamaProvider):
        try:
            info["endpoint"] = p.base_url.split("://", 1)[1].split("/", 1)[0]
        except Exception:
            info["endpoint"] = ""
        present = p._model_present()
        info["server_reachable"] = present is not None
        info["model_available"] = present is True
        info["available"] = present is True
    elif isinstance(p, OpenAICompatProvider):
        info["endpoint"] = p.endpoint_host
        info["auth_configured"] = bool(p.api_key)
    # legacy keys consumed by dashboard/settings/footer
    info["backend"] = p.provider_id
    info["configured"] = selected_id()
    if info["config_errors"]:
        info["detail"] = "; ".join(info["config_errors"])
    elif not p.generative:
        info["detail"] = ("No generation backend reachable; "
                          "evidence-only answers.")
    else:
        info["detail"] = f"{p.provider_id} backend ready"
    return info
