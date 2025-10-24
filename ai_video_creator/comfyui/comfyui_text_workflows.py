"""
This module contains the video workflows for ComfyUI.
"""

import os
from ai_video_creator.comfyui.comfyui_workflow import ComfyUIWorkflowBase


# Get the current directory where this file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_DIR = f"{CURRENT_DIR}/workflows"


class FlorentWorkflowBase(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    SEED_NODE_INDEX = 1
    OUTPUT_NODE_INDEX = 3

    def __init__(
        self,
        workflow: str,
        load_best_config: bool = True,
    ) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(workflow)

        # Loading best configurations for the workflow
        if load_best_config:
            self._load_best_configurations()

    def _load_best_configurations(self) -> None:
        pass

    def set_seed(self, seed: int) -> None:
        """
        Set the seed for the workflow.

        Args:
            seed (int): The seed value to set.
        """
        parameters = {self.SEED_NODE_INDEX: {"seed": seed}}
        self._set_fields(parameters)

    def set_output_filename(self, filename):
        """Set the output filename for the workflow."""
        return super()._set_output_filename(self.OUTPUT_NODE_INDEX, filename)


class FlorentI2TWorkflow(FlorentWorkflowBase):
    """
    Class to handle the workflow for Image to Text in ComfyUI.
    """

    FLORENCE_I2T_WORKFLOW_PATH = f"{WORKFLOW_DIR}/Florence-2-I2T_API.json"

    IMAGE_INPUT_NODE_INDEX = 4

    def __init__(self, load_best_config: bool = True) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(self.FLORENCE_I2T_WORKFLOW_PATH, load_best_config)

    def set_image(self, image_path: str) -> None:
        """
        Set the input image for the workflow.

        Args:
            image_path (str): The path to the input image.
        """
        parameters = {self.IMAGE_INPUT_NODE_INDEX: {"image": image_path}}
        self._set_fields(parameters)


class FlorentV2TWorkflow(FlorentWorkflowBase):
    """
    Class to handle the workflow for Image to Text in ComfyUI.
    """

    FLORENCE_V2T_WORKFLOW_PATH = f"{WORKFLOW_DIR}/Florence-2-V2T_API.json"

    VIDEO_INPUT_NODE_INDEX = 4

    def __init__(self, load_best_config: bool = True) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(self.FLORENCE_V2T_WORKFLOW_PATH, load_best_config)

    def set_video(self, video_path: str) -> None:
        """
        Set the input video for the workflow.

        Args:
            video_path (str): The path to the input video.
        """
        parameters = {self.VIDEO_INPUT_NODE_INDEX: {"video": video_path}}
        self._set_fields(parameters)
