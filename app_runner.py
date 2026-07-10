"""Compatibility wrapper for the main Streamlit app."""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("streamlit_app.py")), run_name="__main__")
