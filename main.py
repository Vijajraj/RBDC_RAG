"""
Root-level proxy main entrypoint for Render.
Ensures 'uvicorn main:app' works if the Render Root Directory is set to the repository root.
"""

import os
import sys

# Add the backend directory to python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.main import app
