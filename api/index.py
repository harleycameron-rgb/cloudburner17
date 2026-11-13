"""Vercel Python entrypoint for the read-only SCANDOC preview.

This imports the isolated FastAPI application only; it does not import
CloudBurner native lifecycle or open any ignition gate.
"""
from backend.scandoc_page import app
