"""
Environment variables for ComfyUI automation module.
"""

import os
from ai_llm import GPT_4oMini_LLM
from dotenv import load_dotenv

load_dotenv()

DESCRIPTION_GENERATION_LLM_MODEL = GPT_4oMini_LLM
BACKGROUND_MUSIC_PROMPT_LLM_MODEL = GPT_4oMini_LLM

DEFAULT_ASSETS_FOLDER = os.getenv("DEFAULT_ASSETS_FOLDER")
if not DEFAULT_ASSETS_FOLDER:
    raise ValueError("DEFAULT_ASSETS_FOLDER environment variable is not set. Please set it in your .env file.")

COMFYUI_INPUT_FOLDER = os.getenv("COMFYUI_INPUT_FOLDER")
if not COMFYUI_INPUT_FOLDER:
    raise ValueError("COMFYUI_INPUT_FOLDER environment variable is not set. Please set it in your .env file.")

COMFYUI_OUTPUT_FOLDER = os.getenv("COMFYUI_OUTPUT_FOLDER")
if not COMFYUI_OUTPUT_FOLDER:
    raise ValueError("COMFYUI_OUTPUT_FOLDER environment variable is not set. Please set it in your .env file.")

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")

TTS_SERVER_URL = os.getenv("TTS_SERVER_URL", "http://127.0.0.1:8189")
