"""
ComfyUI audio workflows.
"""

from .comfyui_audio_workflows import (
    SparkTTSVoiceCloneWorkflow,
    SparkTTSVoiceCreatorWorkflow,
)
from .comfyui_image_workflows import FluxWorkflow
from .comfyui_video_workflows import WanWorkflow

__all__ = [
    "SparkTTSVoiceCloneWorkflow",
    "SparkTTSVoiceCreatorWorkflow",
    "FluxWorkflow",
    "WanWorkflow",
]
