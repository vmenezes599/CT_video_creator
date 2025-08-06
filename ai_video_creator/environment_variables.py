"""
Environment variables for ComfyUI automation module.
"""

import os
from dotenv import load_dotenv

load_dotenv()

COMFYUI_OUTPUT_FOLDER = os.getenv("COMFYUI_OUTPUT_FOLDER")
if not COMFYUI_OUTPUT_FOLDER:
    raise ValueError(
        "COMFYUI_OUTPUT_FOLDER environment variable is not set. Please set it in your .env file."
    )


COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
