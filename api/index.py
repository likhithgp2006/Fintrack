import os
import sys

# Ensure repository root is on sys.path so app and csv_db can be loaded seamlessly
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Export for Vercel Serverless Function runtime
handler = app
