import os
import sys

# ─── Path Setup ──────────────────────────────────────────────────────────────
# In Vercel, api/index.py is the entrypoint but the repo root contains app.py,
# templates/, static/, data/, csv_db.py. We add the root to sys.path.
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)  # one level up from api/

for _p in [_root, _here]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ─── Vercel Flag ─────────────────────────────────────────────────────────────
# Make sure csv_db.py uses /tmp for file storage on the read-only filesystem.
if 'VERCEL' not in os.environ:
    os.environ['VERCEL'] = '1'

# ─── Import Flask App ─────────────────────────────────────────────────────────
try:
    from app import app
except Exception as e:
    # If something goes wrong during import, create a minimal diagnostic app
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/')
    @app.route('/<path:path>')
    def error_handler(path=''):
        return jsonify({
            'error': 'Application failed to start',
            'detail': str(e),
            'type': type(e).__name__,
            'root': _root,
            'sys_path': sys.path[:5],
            'files_in_root': os.listdir(_root) if os.path.exists(_root) else []
        }), 500

# Vercel Python runtime looks for a variable named `app` (WSGI callable)
__all__ = ['app']
