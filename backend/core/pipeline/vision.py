"""Vision escalation hook. The extraction cascade *plans* a vision step for
visual pages (IMAGE_ONLY, IMAGE_TABLE, COMPLEX_LAYOUT); this module
*attempts* it. When a vision-capable model answers (Ollama with a
vision model), the page/figure gains a semantic interpretation with full
provenance. When nothing answers — offline box, text-only model — the
caller records ``vision_skipped`` and keeps the deterministic OCR output.

Nothing here is a substitute for OCR: OCR text and the source image are
always preserved alongside any interpretation.
"""

from __future__ import annotations

import io
import logging
import time

log = logging.getLogger("cmpdi.vision")

_probe_ts = 0.0
_probe_ok = False

# bound per-document cost: never describe more figures than this
MAX_FIGURES_PER_DOC = 5


def _ollama_probe() -> bool:
    """Reachability for the Ollama vision path, delegated to the provider
    so endpoint configuration lives in exactly one place."""
    global _probe_ts, _probe_ok
    if time.time() - _probe_ts < 60:
        return _probe_ok
    _probe_ts = time.time()
    _probe_ok = False
    try:
        from backend.core.llm.providers import OllamaProvider
        p = _provider()
        if isinstance(p, OllamaProvider):
            _probe_ok = p._server_up()
    except Exception:
        pass
    return _probe_ok


def _provider():
    from backend.core.llm import get_provider
    return get_provider()


def available() -> bool:
    """True when a vision attempt is worth making: the selected provider is
    generative, advertises vision support, and (for Ollama) the server is
    reachable. The model itself may still refuse images — that degrades to
    vision_skipped per figure, never an exception."""
    try:
        p = _provider()
        if not p.generative or not p.supports_vision:
            return False
        if p.provider_id == "ollama":
            return _ollama_probe()
        return True
    except Exception:
        return False


def describe_figure(png_bytes: bytes, caption: str = "",
                    ocr_text: str = "") -> dict | None:
    """Describe one figure through the selected provider's vision path.
    Returns the parsed JSON dict on success, None when unavailable,
    refused or unparseable (caller records vision_skipped)."""
    from backend.core.pipeline import vision as _self  # noqa (keeps ref stable)
    del _self
    context = (f"Caption: {caption}\nOCR on figure: {ocr_text[:500]}"
               if (caption or ocr_text) else "Describe this figure.")
    try:
        resp = _provider().describe_image(
            png_bytes,
            "You interpret a figure from a coal/mining/geology report. "
            "Reply with JSON only, no prose, no fences, using exactly these "
            "keys: {\"type\": \"chart|diagram|photo|table|map|other\", "
            "\"title\": \"figure title or empty string\", "
            "\"summary\": \"one sentence describing what the figure shows\", "
            "\"numbers\": [\"verbatim numbers with units seen in the figure\"], "
            "\"trend\": \"increase|decrease|stable|unclear\"}. "
            "If the image is unreadable, reply with type other and empty "
            "strings. " + context,
            caption=caption)
    except Exception as e:
        log.info("Vision Figure Skipped: %s", e)
        return None
    if not resp.ok or not resp.text:
        log.info("Vision Figure Skipped: %s",
                 resp.error.message if resp.error else "empty reply")
        return None
    return _parse_json(resp.text)


def _parse_json(content: str) -> dict | None:
    s = content.strip()
    if s.startswith("```"):
        s = s.strip("`").strip()
        if s.lower().startswith("json"):
            s = s[4:].strip()
    try:
        obj = json.loads(s)
    except Exception:
        start, end = s.find("{"), s.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            obj = json.loads(s[start:end + 1])
        except Exception:
            return None
    if not isinstance(obj, dict) or "type" not in obj:
        return None
    return {
        "type": str(obj.get("type") or "other")[:24],
        "title": str(obj.get("title") or "")[:300],
        "summary": str(obj.get("summary") or "")[:1000],
        "numbers": [str(x)[:120] for x in (obj.get("numbers") or [])][:20],
        "trend": str(obj.get("trend") or "unclear")[:24],
    }


def crop_png(pix, bbox_page: list, zoom: float) -> bytes | None:
    """Crop a page pixmap to a page-coordinate bbox, return PNG bytes."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        x0, y0, x1, y1 = [int(v * zoom) for v in bbox_page]
        w, h = img.size
        box = (max(0, x0), max(0, y0), min(w, max(0, x1)), min(h, max(0, y1)))
        if box[2] <= box[0] or box[3] <= box[1]:
            return None
        buf = io.BytesIO()
        img.crop(box).save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None
