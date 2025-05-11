"""
setup.py
This script is used to package the ComfyUI automation tool as a Python package.
"""
from setuptools import setup, find_packages

setup(
    name="ai_video_creator",
    version="0.2.2",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "comfyui_manager=ai_video_creator.ComfyUI_automation.comfyui_manager:main",
            "ai_video_creator=ai_video_creator.ai_video_creator:main",
        ],
    },
)
