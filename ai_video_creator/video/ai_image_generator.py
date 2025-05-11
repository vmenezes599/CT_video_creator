"""
AI Video Generation Module
"""

from ai_video_creator.ComfyUI_automation.comfyui_requests import ComfyUIRequests
from .ComfyUI_automation.comfyui_flux_story_maker import FluxWorkflow


class FluxAIImageGenerator:
    """
    A class to generate images based on a list of strings using ComfyUI workflows.
    """

    def __init__(self):
        """
        Initialize the AIImageGenerator class.
        """
        self.requests = ComfyUIRequests()  # Initialize ComfyUI requests

    def generate_images(self, prompts: list[str]) -> list[str]:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """
        workflows: list[FluxWorkflow] = []  # Initialize the workflow
        for prompt in prompts:
            # Set the positive prompt in the workflow
            workflow = FluxWorkflow()

            workflow.set_positive_prompt(prompt)

            workflows.append(workflow)

        return self.requests.comfyui_ensure_send_all_prompts(workflows)
