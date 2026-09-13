"""Skill registry: institutional knowledge as loadable packs, not one giant
system prompt. The director lists packs, loads only what the task needs,
and injects the text into planning/writing/audit prompts.

Pack layout: backend/core/reporting/skills/<name>/SKILL.md (+ detail files).
"""

from __future__ import annotations

from pathlib import Path

_SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def list_skills() -> list[dict]:
    out = []
    if not _SKILLS_DIR.exists():
        return out
    for d in sorted(_SKILLS_DIR.iterdir()):
        skill_md = d / "SKILL.md"
        if d.is_dir() and skill_md.exists():
            first = skill_md.read_text().splitlines()
            desc = next((l.strip("# ").strip() for l in first
                         if l.strip() and not l.startswith("#")), d.name)
            # second non-heading line is usually the one-line summary
            lines = [l.strip() for l in first if l.strip()
                     and not l.startswith("#") and not l.startswith("##")]
            out.append({"name": d.name,
                        "description": lines[0] if lines else desc})
    return out


def load_skill(name: str, max_chars: int = 4000) -> str | None:
    """Full pack text (SKILL.md + detail files), truncated for prompts."""
    d = _SKILLS_DIR / name
    if not d.is_dir():
        return None
    parts = []
    for f in sorted(d.glob("*.md")):
        parts.append(f.read_text())
    text = "\n\n".join(parts)
    return text[:max_chars] if len(text) > max_chars else text


def search_skills(query: str) -> list[dict]:
    q = query.lower()
    return [s for s in list_skills()
            if q in s["name"] or q in s["description"].lower()]
