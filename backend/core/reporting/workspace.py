"""Report workspace: the filesystem memory for one report request. The LLM
never has to remember everything — the workspace does:

    workspaces/<id>/
      manifest.json      objective, scope, mode, provider, created
      context.json       working context (entities, metrics, evidence counts)
      plan.json          report plan IR (inspectable before generation)
      evidence.jsonl     evidence graph (claims/data/calcs/sources)
      datasets/          parquet/csv snapshots the analysis ran on
      analysis/          calc records (formula + inputs + values)
      charts/            generated figures
      tables/            csv tables embedded in the report
      drafts/            section drafts (DOM blocks)
      final/             report.docx
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from backend.core import config

SUBDIRS = ("evidence", "datasets", "analysis", "charts", "tables",
           "drafts", "final")


class Workspace:
    def __init__(self, wid: str):
        self.wid = wid
        self.root = config.REPORTS_DIR / "workspaces" / wid

    @classmethod
    def create(cls, objective: str, scope: dict, mode: str,
               provider: str, model: str) -> "Workspace":
        ws = cls(uuid.uuid4().hex[:12])
        for sub in SUBDIRS:
            (ws.root / sub).mkdir(parents=True, exist_ok=True)
        ws.write_json("manifest.json", {
            "id": ws.wid, "objective": objective, "scope": scope,
            "mode": mode, "provider": provider, "model": model,
            "created_ts": time.strftime("%Y-%m-%d %H:%M:%S")})
        return ws

    # -- json helpers -------------------------------------------------------

    def _p(self, *parts) -> Path:
        return self.root.joinpath(*parts)

    def write_json(self, name: str, obj) -> Path:
        p = self._p(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, indent=2, default=str))
        return p

    def read_json(self, name: str, default=None):
        p = self._p(name)
        if not p.exists():
            return default
        try:
            return json.loads(p.read_text())
        except Exception:
            return default

    def evidence_path(self) -> Path:
        return self._p("evidence", "evidence.jsonl")

    def chart_path(self, name: str) -> Path:
        return self._p("charts", name)

    def table_path(self, name: str) -> Path:
        return self._p("tables", name)

    def dataset_path(self, name: str) -> Path:
        return self._p("datasets", name)

    def final_docx(self, stem: str = "report") -> Path:
        return self._p("final", f"{stem}.docx")


def build_context(objective: str, scope: dict) -> dict:
    """Working context: everything the planner needs on one page — scope,
    library contents, known conflicts — computed deterministically from
    the knowledge layer, never hallucinated."""
    from backend.core.llm import tools as _tools  # local import: tools package
    from backend.db import database as db

    summary = _tools.get("entity_summary").run(
        {"query": scope.get("entity") or ""})
    conflicts = db.q("""
        SELECT COALESCE(e.canonical_name, f.entity_text) AS entity,
               f.attribute, COUNT(DISTINCT f.value_norm) n
        FROM facts f LEFT JOIN entities e ON e.id = f.entity_id
        WHERE f.value_norm IS NOT NULL
        GROUP BY entity, f.attribute, f.period_norm HAVING n > 1
        LIMIT 50""")
    docs = db.q("""SELECT id, filename, display_name, doc_type, subsidiary
                   FROM documents WHERE status='completed'
                   ORDER BY upload_ts DESC LIMIT 40""")
    return {
        "objective": objective,
        "scope": scope,
        "library": {"documents": summary.get("documents", 0),
                    "sample": [{"id": d["id"],
                                "name": d["display_name"] or d["filename"],
                                "type": d["doc_type"],
                                "subsidiary": d["subsidiary"]} for d in docs]},
        "entities": summary.get("entities", []),
        "metrics": summary.get("attributes", []),
        "periods": summary.get("periods", []),
        "known_conflicts": [
            {"entity": c["entity"], "attribute": c["attribute"],
             "variants": c["n"]} for c in conflicts],
        "requirements": ["executive summary", "sourced analysis sections",
                         "charts with units", "verification notes",
                         "sources appendix with receipts"],
        "style": "Government technical report: plain sentences, fiscal-year "
                 "labels, MT units, no adjectives without numbers.",
    }
