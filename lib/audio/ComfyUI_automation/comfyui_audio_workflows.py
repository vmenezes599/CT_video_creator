import json
import random
from typing_extensions import override

from lib.ComfyUI_automation.comfyui_workflow import ComfyUIWorkflowBase
from .environment_variables import WORKFLOW_JSON_DIR


class SparkTTSWorkflowBase(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    def __init__(self, base_workflow: str):
        """
        Initialize the FluxWorkflow class.
        """
        super().__init__(base_workflow)
