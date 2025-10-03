"""
ComfyUI audio workflows.
"""

from .comfyui_image_workflows import FluxWorkflow
from .comfyui_video_workflows import (
    WanI2VWorkflow,
    WanV2VWorkflow,
    WanT2VWorkflow,
    VideoUpscaleFrameInterpWorkflow,
)

__all__ = [
    "FluxWorkflow",
    "WanI2VWorkflow",
    "WanV2VWorkflow",
    "WanT2VWorkflow",
    "VideoUpscaleFrameInterpWorkflow",
]
