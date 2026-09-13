"""LLM diagnostics API. All output is safe to display: provider/model
names, endpoint hostnames, capability flags and test status. API keys,
tokens and prompts never appear here."""

from flask import Blueprint, jsonify, request

from backend.core.llm import get_provider, safe_status

bp = Blueprint("llm", __name__)


@bp.get("/api/llm/status")
def status():
    """Cheap config snapshot of the selected backend (no inference)."""
    return jsonify(safe_status())


@bp.post("/api/llm/check")
def check():
    """Run the minimal live inference probe. Optional JSON body:
    {"provider": "ollama|huggingface|openai_compatible"} to check one
    backend instead of the selected one."""
    data = request.get_json(silent=True) or {}
    pid = (data.get("provider") or "").strip() or None
    try:
        provider = get_provider(pid)
    except Exception as e:
        return jsonify({"provider": pid, "inference_ok": False,
                        "failure": f"{type(e).__name__}: {e}"}), 400
    result = provider.health_check()
    return jsonify(result), (200 if result.get("inference_ok") else 503)
