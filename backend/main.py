"""
Proxy main entrypoint for Render.
Enables running 'uvicorn main:app' from the backend root directory.
"""

from app.main import app
