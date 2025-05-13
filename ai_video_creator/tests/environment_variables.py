import os
from dotenv import load_dotenv

load_dotenv()
TEST_COMFYUI_PATH = os.getenv("TEST_COMFYUI_PATH")
TEST_COMFYUI_BASE_PATH = os.getenv("TEST_COMFYUI_BASE_PATH")
COMFYUI_OUTPUT_FOLDER = os.path.abspath("outputs/ComfyUI")

TEST_SYS_ARGV = [
    "comfyui_server_manager.py",
    "--comfyui-path",
    TEST_COMFYUI_PATH,
    "--base-directory",
    TEST_COMFYUI_BASE_PATH,
    "--output-directory",
    COMFYUI_OUTPUT_FOLDER,
]
