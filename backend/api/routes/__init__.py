"""Blueprint registry: every route package registers its blueprint here and
the application factory mounts the list in order. ``pages`` carries the
screen-data endpoints for the React SPA, ``actions`` the JSON mutations."""

from backend.api.routes import (actions, agent, chat, compare, conflicts,
                                documents, ingest, pages, reports)

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
]
