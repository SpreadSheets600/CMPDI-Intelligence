"""Blueprint registry: every route package registers its blueprint here and
the application factory mounts the list in order."""

from backend.api.routes import (agent, ask, chat, compare, conflicts,
                                dashboard, documents, ingest, insights,
                                landing, reports, search, settings, topics)

ALL_BLUEPRINTS = [
    landing.bp,
    dashboard.bp,
    ingest.bp,
    documents.bp,
    search.bp,
    ask.bp,
    chat.bp,
    insights.bp,
    topics.bp,
    reports.bp,
    agent.bp,
    settings.bp,
    conflicts.bp,
    compare.bp,
]
