---
description: 'Flask JSON API conventions for CMPDI Intelligence: thin Blueprint routes, stable response shapes, receipt links'
applyTo: 'backend/api/**/*.py'
---

# Flask API Development

One Flask process serves the SPA plus the JSON API. Each module in `backend/api/` owns a `bp` Blueprint, registered in order in `backend/api/__init__.py` (`ALL_BLUEPRINTS`) and mounted by the factory in `backend/app/__init__.py`.

## General Instructions

- Keep routes thin: validate input, call exactly one service function, return the result. No domain computation in handlers.
- Distinguish endpoint kinds: `/api/pages/*` returns initial screen state; live endpoints (`/api/jobs`, `/api/chat`, `/api/conflicts`, …) serve interaction and polling.
- Never change a response shape casually; if a contract changes, update frontend and backend together.

## Best Practices

- Read query args defensively: `(request.args.get("x") or "").strip() or None`.
- Return errors as `jsonify({"error": "..."})` with 400 (bad input) or 404 (unknown id); the frontend throws on non-2xx.
- Every evidence-bearing response must include receipt fields (`doc_id`, `page_no`/`sheet_no`, `chunk_id`, `filename`) so the UI can deep-link into the Source Viewer.
- Register every new blueprint in `ALL_BLUEPRINTS`; keep the module docstring to one line stating the endpoint's purpose.

```python
@bp.get("/api/things")
def api_things():
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    result = things.describe(name)
    if not result:
        return jsonify({"error": "unknown thing"}), 404
    return jsonify(result)
```

## Validation

- Exercise each route (happy path, missing param, unknown id) against a scratch database before committing.
- Confirm polling endpoints stay cheap: bounded `LIMIT`, indexed columns, no unbounded serialization.
