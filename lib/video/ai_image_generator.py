"""
AI Video Generation Module
"""

import os

from .AI.ComfyUI_automation.comfyui_flux_story_maker import FluxWorkflow
from .AI.ComfyUI_automation.features.comfyui_requests import ComfyUIRequests
from .AI.ComfyUI_automation.features.environment_variables import CONFYUI_URL


class FluxAIImageGenerator:
    """
    A class to generate images based on a list of strings using ComfyUI workflows.
    """

    def __init__(self, output_folder: str):
        """
        Initialize the AIImageGenerator class.

        :param output_folder: The folder where generated images will be saved.
        """
        self.output_folder = output_folder
        os.makedirs(
            self.output_folder, exist_ok=True
        )  # Ensure the output folder exists
        self.workflows = list[FluxWorkflow]  # Initialize the workflow
        self.requests = ComfyUIRequests(CONFYUI_URL)  # Initialize ComfyUI requests

    def generate_images(self, prompts: list[str]) -> list[str]:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """

        for index, prompt in enumerate(prompts):
            # Set the positive prompt in the workflow
            workflow = FluxWorkflow()

            workflow.set_positive_prompt(prompt)
            workflow.set_output_filename(f"test{index}")
  
        image_paths = []
            


        return image_paths
