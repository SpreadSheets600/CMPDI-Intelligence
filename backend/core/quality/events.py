"""Append-only event log behind the measured automation metrics.

Kinds: report_generated / report_approved / report_returned /
conflict_acknowledged / conflict_resolved / conflict_reopened /
answer_grounded / answer_agent / answer_abstained. Logging never raises:
a metrics write must not break the request that triggered it.
"""

import json
import logging

from backend.db import database as db

log = logging.getLogger("cmpdi.events")


def record(
    kind: str, ref_id: str | int | None = None, detail: dict | None = None
) -> None:
    try:
        db.execute(
            "INSERT INTO events (kind, ref_id, detail_json) VALUES (?,?,?)",
            (kind, None if ref_id is None else str(ref_id), json.dumps(detail or {})),
        )
    except Exception:
        log.warning("Event Not Recorded: %s", kind, exc_info=True)


def count(kind: str) -> int:
    row = db.q1("SELECT COUNT(*) c FROM events WHERE kind=?", (kind,))
    return row["c"] if row else 0
