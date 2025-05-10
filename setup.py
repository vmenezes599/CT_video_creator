"""
setup.py
This script is used to package the ComfyUI automation tool as a Python package.
"""
from setuptools import setup, find_packages

setup(
    name="ai_video_creator",
    version="0.2.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "comfyui_manager=lib.ComfyUI_automation.comfyui_manager:main",
        ],
    },
)
