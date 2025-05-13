"""
Environment variables for ComfyUI automation module.
"""

import os

COMFYUI_OUTPUT_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../outputs/ComfyUI")
)
