"""Document file serving: untouched originals and extracted page images.
The library screens themselves live in the React SPA (see backend/api/pages)."""

from flask import Blueprint, abort, send_file, send_from_directory

from backend import storage
from backend.core import config

bp = Blueprint("documents", __name__)


@bp.route("/documents/<doc_id>/original")
def original(doc_id):
    """Serves the untouched original so the browser can render native
    previews (PDF viewer) and users can download the source of truth."""
    path = storage.original_path(doc_id)
    if path is None:
        abort(404)
    return send_file(path, download_name=path.name)


@bp.route("/page_image/<doc_id>/<path:rel>")
def page_image(doc_id, rel):
    return send_from_directory(config.FILES_DIR, f"{doc_id}/{rel}")
