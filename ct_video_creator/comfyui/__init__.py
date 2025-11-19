"""Automation utilities for ComfyUI."""

from .comfyui_requests import ComfyUIRequests

from .comfyui_text_workflows import (
    FlorentI2TWorkflow,
    FlorentV2TWorkflow,
    FlorentWorkflowBase,
)
from .comfyui_image_workflows import FluxWorkflow
from .comfyui_video_workflows import (
    WanI2VWorkflow,
    WanT2VWorkflow,
    VideoUpscaleFrameInterpWorkflow,
)

__all__ = [
    "ComfyUIRequests",
    "FluxWorkflow",
    "WanI2VWorkflow",
    "WanT2VWorkflow",
    "VideoUpscaleFrameInterpWorkflow",
    "FlorentI2TWorkflow",
    "FlorentV2TWorkflow",
    "FlorentWorkflowBase",
]
