"""Vercel entrypoint - re-exports FastAPI app from web/app.py."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import app
