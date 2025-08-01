"""
AI Video Generation Module
"""

from ai_video_creator.ComfyUI_automation.comfyui_requests import ComfyUIRequests
from ai_video_creator.environment_variables import COMFYUI_OUTPUT_FOLDER

from .ComfyUI_automation.comfyui_image_workflows import FluxWorkflow


class FluxAIImageGenerator:
    """
    A class to generate images based on a list of strings using ComfyUI workflows.
    """

    def __init__(self):
        """
        Initialize the AIImageGenerator class.
        """
        self.requests = ComfyUIRequests()  # Initialize ComfyUI requests

    def text_to_image(self, prompts: list[str], output_file_name: str) -> list[str]:
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
            workflow.set_output_filename(output_file_name)

            workflows.append(workflow)

        output_file_names = self.requests.comfyui_ensure_send_all_prompts(workflows)

        for file_name in output_file_names:
            file_name = f"{COMFYUI_OUTPUT_FOLDER}/{file_name}"

        return output_file_names
