"""Blueprint registry: every API module registers its blueprint here and
the application factory mounts the list in order. ``pages`` carries the
screen-data endpoints for the React SPA, ``actions`` the JSON mutations."""

from backend.api import (
    actions,
    agent,
    assets,
    chat,
    compare,
    conflicts,
    documents,
    ingest,
    insights,
    llm,
    pages,
    reference,
    reports,
    search,
    temporal,
)

ALL_BLUEPRINTS = [
    pages.bp,
    actions.bp,
    ingest.bp,
    documents.bp,
    chat.bp,
    reports.bp,
    agent.bp,
    conflicts.bp,
    compare.bp,
    insights.bp,
    llm.bp,
    reference.bp,
    search.bp,
    assets.bp,
    temporal.bp,
]
