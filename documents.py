import os
from flask import Blueprint
from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, jsonify, make_response, current_app, session, abort)
from flask_session import Session

documents_bp = Blueprint('documents', __name__)


"""
REDIRECCIONAMIENTO A REPOSITORIO DE REACT
"""

def _find_frontend_static_dir():
    frontend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'DocumentosApp', 'frontend'))
    dist_dir = os.path.join(frontend_root, 'dist')
    build_dir = os.path.join(frontend_root, 'build')
    if os.path.isdir(dist_dir):
        return dist_dir
    if os.path.isdir(build_dir):
        return build_dir
    return None


@documents_bp.route('/documents', defaults={'path': ''})
@documents_bp.route('/documents/<path:path>')
def serve_react_app(path: str):
    """Serve React build files.

    This will serve files from the React build folder located at
    ../DocumentosApp/frontend/build relative to this file. If the
    requested path exists in the build folder it will be returned
    (useful for /documents/static/js/...), otherwise index.html is
    returned so React Router can handle client-side routes.
    """
    # Frontend output directories: Vite uses `dist`, CRA uses `build`.
    frontend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'DocumentosApp', 'frontend'))
    static_dir = _find_frontend_static_dir()

    if static_dir is None:
        message = (
            "Frontend build not found. Build the frontend and place the output folder (`dist` or `build`) at:\n"
            f"{frontend_root}\n\n"
            "Commands (from DocumentosApp/frontend):\n"
            "npm install ; npm run build\n"
            "For Vite the output will be `dist`, for CRA it's `build`.\n"
        )
        return (message, 500)

    # If the requested file exists in the static directory, serve it
    requested_file = os.path.join(static_dir, path)
    if path and os.path.exists(requested_file) and os.path.isfile(requested_file):
        # Compute relative path inside static_dir
        rel_path = os.path.relpath(requested_file, static_dir)
        return send_from_directory(static_dir, rel_path)

    # Otherwise serve index.html so client-side routing works
    index_path = os.path.join(static_dir, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_dir, 'index.html')

    # Fallback (should not normally happen)
    abort(404)


@documents_bp.route('/assets/<path:filename>')
def serve_frontend_assets(filename: str):
    """Serve frontend assets when index.html references root-relative /assets/... URLs."""
    static_dir = _find_frontend_static_dir()
    if static_dir is None:
        abort(404)

    assets_dir = os.path.join(static_dir, 'assets')
    requested = os.path.join(assets_dir, filename)
    if os.path.exists(requested) and os.path.isfile(requested):
        return send_from_directory(assets_dir, filename)

    abort(404)

"""
Fin de redireccionamiento a repositorio de React
"""