"""Evidence graph: every report claim resolves to data, calculations and
sources through stable IDs.

    CLAIM-001 (prose statement)
      |-- DATA-001/002 (reported values with receipts)
      |-- CALC-001     (deterministic derivation: formula + inputs)
      |-- SOURCE-001/2 (document, page/sheet, chunk)

The graph is append-only JSONL inside the report workspace (evidence.jsonl)
so the auditor, the reviewer UI and future chat turns can re-resolve any
claim without re-running retrieval.
"""

from __future__ import annotations

import json
from pathlib import Path


class EvidenceGraph:
    def __init__(self, path: Path | None = None):
        self.path = path
        self.claims: dict[str, dict] = {}
        self.data: dict[str, dict] = {}
        self.calcs: dict[str, dict] = {}
        self.sources: dict[str, dict] = {}
        if path and path.exists():
            self._load()

    # -- builders ---------------------------------------------------------

    def add_source(self, doc_id, filename, page_no=None, sheet_no=None,
                   chunk_id=None, value_raw: str = "",
                   unit: str = "") -> str:
        sid = f"SOURCE-{len(self.sources) + 1:03d}"
        self.sources[sid] = {"id": sid, "doc_id": doc_id,
                             "filename": filename, "page_no": page_no,
                             "sheet_no": sheet_no, "chunk_id": chunk_id,
                             "value_raw": value_raw, "unit": unit or ""}
        self._append("source", self.sources[sid])
        return sid

    def add_data(self, label: str, value_raw: str, value_norm,
                 unit: str, source_ids: list[str]) -> str:
        did = f"DATA-{len(self.data) + 1:03d}"
        self.data[did] = {"id": did, "label": label, "value_raw": value_raw,
                          "value_norm": value_norm, "unit": unit or "",
                          "sources": list(source_ids)}
        self._append("data", self.data[did])
        return did

    def add_calc(self, metric: str, value, unit: str, formula: str,
                 inputs: dict, data_ids: list[str]) -> str:
        cid = f"CALC-{len(self.calcs) + 1:03d}"
        self.calcs[cid] = {"id": cid, "metric": metric, "value": value,
                           "unit": unit or "", "formula": formula,
                           "inputs": inputs, "data": list(data_ids)}
        self._append("calc", self.calcs[cid])
        return cid

    def add_claim(self, text: str, data_ids: list[str],
                  calc_ids: list[str]) -> str:
        cid = f"CLAIM-{len(self.claims) + 1:03d}"
        srcs: list[str] = []
        for did in data_ids:
            srcs.extend(self.data.get(did, {}).get("sources", []))
        self.claims[cid] = {"id": cid, "text": text, "data": list(data_ids),
                            "calcs": list(calc_ids),
                            "sources": sorted(set(srcs))}
        self._append("claim", self.claims[cid])
        return cid

    # -- resolution ---------------------------------------------------------

    def resolve_claim(self, claim_id: str) -> dict | None:
        c = self.claims.get(claim_id)
        if not c:
            return None
        return {"claim": c,
                "data": [self.data[d] for d in c["data"] if d in self.data],
                "calcs": [self.calcs[x] for x in c["calcs"] if x in self.calcs],
                "sources": [self.sources[s] for s in c["sources"]
                            if s in self.sources]}

    def receipt_refs(self) -> dict:
        """Provenance slots compatible with the reports review UI
        (ref -> doc/page/sheet)."""
        refs = {}
        for i, sid in enumerate(sorted(self.sources), 1):
            s = self.sources[sid]
            refs[f"S{i}"] = {"doc_id": s["doc_id"], "page_no": s["page_no"],
                             "sheet_no": s["sheet_no"]}
        return refs

    def summary(self) -> dict:
        return {"claims": len(self.claims), "data": len(self.data),
                "calcs": len(self.calcs), "sources": len(self.sources)}

    # -- persistence ----------------------------------------------------------

    def _append(self, kind: str, record: dict):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps({"kind": kind, **record}, default=str) + "\n")

    def _load(self):
        assert self.path is not None
        for line in self.path.read_text().splitlines():
            try:
                rec = json.loads(line)
            except Exception:
                continue
            kind = rec.pop("kind", "")
            store = {"claim": self.claims, "data": self.data,
                     "calc": self.calcs, "source": self.sources}.get(kind)
            if store is not None and rec.get("id"):
                store[rec["id"]] = rec
