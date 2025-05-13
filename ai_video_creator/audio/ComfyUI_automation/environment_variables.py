"""
Environment variables for ComfyUI automation module.
"""

import os

CONFYUI_URL = "http://127.0.0.1:8188/"  # Default ComfyUI local API

WORKFLOW_JSON_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "workflows")
)
