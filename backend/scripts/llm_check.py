"""Provider diagnostics: validate configuration and run a cheap live
inference probe per backend. Never prints secrets — endpoint appears as
host only, API keys as set/unset flags.

Usage:
    python -m backend.scripts.llm_check                  # selected backend
    python -m backend.scripts.llm_check --provider ollama
    python -m backend.scripts.llm_check --provider all
    python -m backend.scripts.llm_check --no-inference   # config only

Exit code is 0 only when every checked provider passes inference
(or validation, with --no-inference).
"""

from __future__ import annotations

import argparse
import json
import sys


def check_one(provider_id: str, inference: bool) -> dict:
    from backend.core.llm import get_provider
    try:
        provider = get_provider(provider_id)
    except Exception as e:
        return {"provider": provider_id, "error": f"{type(e).__name__}: {e}"}
    if not inference:
        errs = provider.validate()
        out = {"provider": provider.provider_id, "model": provider.model,
               "generative": provider.generative,
               "vision": provider.supports_vision,
               "structured": provider.supports_structured,
               "config_valid": not errs, "config_errors": errs}
        if hasattr(provider, "endpoint_host"):
            out["endpoint"] = provider.endpoint_host
            out["auth_configured"] = bool(
                getattr(provider, "api_key", ""))
        return out
    return provider.health_check()


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM provider diagnostics")
    parser.add_argument("--provider", default=None,
                        help="ollama|huggingface|openai_compatible|all "
                             "(default: selected backend)")
    parser.add_argument("--no-inference", action="store_true",
                        help="validate configuration only, no model calls")
    args = parser.parse_args()

    if args.provider in (None, "selected"):
        ids = [None]
    elif args.provider == "all":
        ids = ["ollama", "huggingface", "openai_compatible"]
    else:
        ids = [args.provider]

    results = [check_one(pid, not args.no_inference) for pid in ids]
    print(json.dumps(results if len(results) > 1 else results[0], indent=2))
    if args.no_inference:
        ok = all(r.get("config_valid", False) for r in results)
    else:
        ok = all(r.get("inference_ok", False) for r in results)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
