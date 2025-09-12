"""
This module contains the video workflows for ComfyUI.
"""

import os
from ai_video_creator.ComfyUI_automation.comfyui_workflow import ComfyUIWorkflowBase


# Get the current directory where this file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_DIR = f"{CURRENT_DIR}/workflows"


class WanWorkflowBase(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    SEED_NODE_INDEX = 7
    POSITIVE_PROMPT_NODE_INDEX = 12
    OUTPUT_FILENAME_NODE_INDEX = 20

    def __init__(self, workflow: str, load_best_config: bool = True) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(workflow)

        # Loading best configurations for the workflow
        if load_best_config:
            self._load_best_configurations()

    def _load_best_configurations(self) -> None:
        pass

    def set_seed(
        self,
        seed: int,
    ) -> None:
        """
        Set the seed sweeper to the JSON configuration.
        """
        parameters = {
            self.SEED_NODE_INDEX: {
                "noise_seed": seed,
            }
        }
        super()._set_fields(parameters)

    def set_positive_prompt(
        self,
        positive_prompt: str,
    ) -> None:
        """
        Set the positive prompt sweeper to the JSON configuration.
        """

        parameters = {
            self.POSITIVE_PROMPT_NODE_INDEX: {
                "text": positive_prompt,
            }
        }
        super()._set_fields(parameters)

    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """
        parameters = {
            self.OUTPUT_FILENAME_NODE_INDEX: {
                "filename_prefix": filename,
            }
        }
        super()._set_fields(parameters)


class WanI2VWorkflow(WanWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    WAN_LORA_WORKFLOW_PATH = f"{WORKFLOW_DIR}/WAN2.2-I2V_API.json"

    LOAD_IMAGE_NODE_INDEX = 14

    def __init__(self, load_best_config: bool = True) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(self.WAN_LORA_WORKFLOW_PATH)

        # Loading best configurations for the workflow
        if load_best_config:
            self._load_best_configurations()

    def _load_best_configurations(self) -> None:
        pass

    def set_image_path(self, image_path: str) -> None:
        """
        Set the input image path.
        """
        parameters = {
            self.LOAD_IMAGE_NODE_INDEX: {
                "image": image_path,
            }
        }
        super()._set_fields(parameters)


class WanV2VWorkflow(WanWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    WAN_LORA_WORKFLOW_PATH = f"{WORKFLOW_DIR}/WAN2.2-I2V_API.json"

    LOAD_VIDEO_NODE_INDEX = 46

    def __init__(self, load_best_config: bool = True) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(self.WAN_LORA_WORKFLOW_PATH)

        # Loading best configurations for the workflow
        if load_best_config:
            self._load_best_configurations()

    def _load_best_configurations(self) -> None:
        pass

    def set_video_path(self, video_path: str) -> None:
        """
        Set the input video path.
        """
        parameters = {
            self.LOAD_VIDEO_NODE_INDEX: {
                "video": video_path,
            }
        }
        super()._set_fields(parameters)
