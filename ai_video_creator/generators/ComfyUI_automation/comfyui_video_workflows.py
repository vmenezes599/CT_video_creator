"""
This module contains the video workflows for ComfyUI.
"""

from collections import deque
import os
from ai_video_creator.ComfyUI_automation.comfyui_workflow import ComfyUIWorkflowBase


# Get the current directory where this file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_DIR = f"{CURRENT_DIR}/workflows"


class WanWorkflowBase(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    def __init__(
        self,
        workflow: str,
        first_high_lora_node_index: int,
        first_low_lora_node_index: int,
        load_best_config: bool = True,
    ) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(workflow)

        self.last_high_lora_node_index = first_high_lora_node_index
        self.last_low_lora_node_index = first_low_lora_node_index

        # Loading best configurations for the workflow
        if load_best_config:
            self._load_best_configurations()

    def _load_best_configurations(self) -> None:
        pass

    def _set_seed(
        self,
        seed_node_index: int,
        seed: int,
    ) -> None:
        """
        Set the seed sweeper to the JSON configuration.
        """
        parameters = {
            seed_node_index: {
                "noise_seed": seed,
            }
        }
        super()._set_fields(parameters)

    def _set_positive_prompt(
        self,
        positive_prompt_node_index: int,
        positive_prompt: str,
    ) -> None:
        """
        Set the positive prompt sweeper to the JSON configuration.
        """

        parameters = {
            positive_prompt_node_index: {
                "text": positive_prompt,
            }
        }
        super()._set_fields(parameters)

    def _set_resolution(
        self,
        resolution_node_index: int,
        width: int,
        height: int,
    ) -> None:
        """
        Set the resolution for the workflow.
        """
        parameters = {
            resolution_node_index: {
                "width": width,
                "height": height,
            }
        }
        super()._set_fields(parameters)

    def _generate_new_lora_node_dict(
        self, lora_name: str, strength: float, previous_link: int
    ) -> dict:
        """Get a dictionary of LORA nodes in the workflow."""
        lora_dict = {
            "inputs": {
                "lora_name": lora_name,
                "strength_model": strength,
                "model": [str(previous_link), 0],
            },
            "class_type": "LoraLoaderModelOnly",
            "_meta": {"title": "LoraLoaderModelOnly"},
        }

        workflow_keys = self.workflow.keys()
        last_key = deque(workflow_keys)[-1]
        new_last_key = str(int(last_key) + 1)

        return {new_last_key: lora_dict}

    def _remove_node(self, to_remove_index: int, output_rewire_list: list[str]):
        """
        Remove a node from the workflow and rewire the outputs.
        """
        to_remove_index_str = str(to_remove_index)
        if to_remove_index_str not in self.workflow.keys():
            raise ValueError(f"Node index {to_remove_index} not found in the workflow.")

        # Rewire the outputs
        for output_node in output_rewire_list:
            if output_node not in self.workflow[to_remove_index_str]["inputs"]:
                raise ValueError(
                    f"Output node {output_node} not found in the inputs of node {to_remove_index}."
                )

            list_of_connections: list[str] = self.workflow[to_remove_index_str][
                "inputs"
            ][output_node]
            list_of_connections_to_rewire = []
            for index in range(0, len(list_of_connections), 2):
                list_of_connections_to_rewire.append(list_of_connections[index])

            for to_rewire in list_of_connections_to_rewire:
                self._replace_model_node_reference(
                    to_remove_index, int(to_rewire), ["images"]
                )

        del self.workflow[to_remove_index_str]

    def add_high_lora(self, high_lora_name: str, strength: float) -> None:
        """Add high LORA to the workflow."""
        new_entry = self._generate_new_lora_node_dict(
            high_lora_name, strength, self.last_high_lora_node_index
        )

        new_entry_key = int(deque(new_entry.keys())[-1])
        self._replace_model_node_reference(
            self.last_high_lora_node_index, new_entry_key, ["model"]
        )

        self.workflow.update(new_entry)
        self.last_high_lora_node_index = new_entry_key

    def add_low_lora(self, low_lora_name: str, strength: float) -> None:
        """Add low LORA to the workflow."""
        new_entry = self._generate_new_lora_node_dict(
            low_lora_name, strength, self.last_low_lora_node_index
        )

        new_entry_key = int(deque(new_entry.keys())[-1])
        self._replace_model_node_reference(
            self.last_low_lora_node_index, new_entry_key, ["model"]
        )

        self.workflow.update(new_entry)
        self.last_low_lora_node_index = new_entry_key


class WanI2VWorkflow(WanWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    WAN_I2V_WORKFLOW_PATH = f"{WORKFLOW_DIR}/WAN2.2-I2V_API.json"

    SEED_NODE_INDEX = 7
    POSITIVE_PROMPT_NODE_INDEX = 12
    OUTPUT_FILENAME_NODE_INDEX = 20
    RESOLUTION_NODE_INDEX = 15
    LOAD_IMAGE_NODE_INDEX = 14
    FIRST_HIGH_LORA_NODE_INDEX = 3
    FIRST_LOW_LORA_NODE_INDEX = 4

    def __init__(self, load_best_config: bool = True) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(
            self.WAN_I2V_WORKFLOW_PATH,
            self.FIRST_HIGH_LORA_NODE_INDEX,
            self.FIRST_LOW_LORA_NODE_INDEX,
        )

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

    def set_seed(self, seed: int) -> None:
        """
        Set the seed for the workflow.
        """
        self._set_seed(self.SEED_NODE_INDEX, seed)

    def set_positive_prompt(self, positive_prompt: str) -> None:
        """
        Set the positive prompt for the workflow.
        """
        self._set_positive_prompt(self.POSITIVE_PROMPT_NODE_INDEX, positive_prompt)

    def set_resolution(self, width: int, height: int) -> None:
        """
        Set the resolution for the workflow.
        """
        self._set_resolution(self.RESOLUTION_NODE_INDEX, width, height)

    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """
        self._set_output_filename(self.OUTPUT_FILENAME_NODE_INDEX, filename)


class WanT2VWorkflow(WanWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    WAN_T2V_WORKFLOW_PATH = f"{WORKFLOW_DIR}/WAN2.2-T2V_API.json"

    SEED_NODE_INDEX = 13
    POSITIVE_PROMPT_NODE_INDEX = 10
    OUTPUT_FILENAME_NODE_INDEX = 17
    RESOLUTION_NODE_INDEX = 30
    FIRST_HIGH_LORA_NODE_INDEX = 2
    FIRST_LOW_LORA_NODE_INDEX = 4

    def __init__(self, load_best_config: bool = True) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(
            self.WAN_T2V_WORKFLOW_PATH,
            self.FIRST_HIGH_LORA_NODE_INDEX,
            self.FIRST_LOW_LORA_NODE_INDEX,
        )

        # Loading best configurations for the workflow
        if load_best_config:
            self._load_best_configurations()

    def _load_best_configurations(self) -> None:
        pass

    def set_seed(self, seed: int) -> None:
        """
        Set the seed for the workflow.
        """
        self._set_seed(self.SEED_NODE_INDEX, seed)

    def set_positive_prompt(self, positive_prompt: str) -> None:
        """
        Set the positive prompt for the workflow.
        """
        self._set_positive_prompt(self.POSITIVE_PROMPT_NODE_INDEX, positive_prompt)

    def set_resolution(self, width: int, height: int) -> None:
        """
        Set the resolution for the workflow.
        """
        self._set_resolution(self.RESOLUTION_NODE_INDEX, width, height)

    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """
        self._set_output_filename(self.OUTPUT_FILENAME_NODE_INDEX, filename)


class VideoUpscaleFrameInterpWorkflow(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for video upscaling and frame interpolation in ComfyUI.
    """

    VIDEO_UPSCALE_FRAME_INTERP_WORKFLOW_PATH = (
        f"{WORKFLOW_DIR}/Video-Upscale-FrameInterp_API.json"
    )

    OUTPUT_FILENAME_NODE_INDEX = 4
    LOAD_VIDEO_NODE_INDEX = 5

    def __init__(self, load_best_config: bool = True) -> None:
        """
        Initialize the VideoUpscaleFrameInterpWorkflow class.
        """
        super().__init__(self.VIDEO_UPSCALE_FRAME_INTERP_WORKFLOW_PATH)

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

    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename for the generated video.
        """
        self._set_output_filename(self.OUTPUT_FILENAME_NODE_INDEX, filename)
