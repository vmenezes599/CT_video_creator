"""
This module contains the Florence image generator class."""

import random

from pathlib import Path
from logging_utils import logger

from ai_video_creator.ComfyUI_automation import ComfyUIRequests
from ai_video_creator.ComfyUI_automation import (
    copy_media_to_comfyui_input_folder,
    delete_media_from_comfyui_input_folder,
)

from .ComfyUI_automation.comfyui_text_workflows import (
    FlorentI2TWorkflow,
    FlorentV2TWorkflow,
)

from ai_video_creator.environment_variables import COMFYUI_OUTPUT_FOLDER


class FlorenceGenerator:
    """
    A class to generate videos based on a list of strings using ComfyUI workflows.
    """

    def __init__(self):
        """
        Initialize the WanGenerator class.
        :param generation_count: Number of passes of WAN. Each passes adds 5 second of video.
        """
        self.requests = ComfyUIRequests()  # Initialize ComfyUI requests

    def generate_description(self, asset: Path) -> str:
        """
        Generate a description based on the input image.
        """

        new_asset_path = copy_media_to_comfyui_input_folder(asset)

        workflow = None
        if asset.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            workflow = FlorentI2TWorkflow()
            workflow.set_image(new_asset_path.name)
        elif asset.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
            workflow = FlorentV2TWorkflow()
            workflow.set_video(new_asset_path.name)
        else:
            logger.error(f"Unsupported asset type: {asset.suffix}")
            raise ValueError(f"Unsupported asset type: {asset.suffix}")

        temp_file_name = Path(f"florence_output_{random.randint(0, 2**32 - 1)}.txt")

        workflow.set_seed(random.randint(0, 2**64 - 1))
        workflow.set_output_filename(temp_file_name.stem)

        self.requests.comfyui_ensure_send_all_prompts([workflow])

        delete_media_from_comfyui_input_folder(new_asset_path)

        output_text_path = None
        for file in Path(COMFYUI_OUTPUT_FOLDER).iterdir():
            if temp_file_name.stem in file.stem:
                output_text_path = file
                break

        with open(output_text_path, "r", encoding="utf-8") as file_handler:
            result = file_handler.read().strip()

        output_text_path.unlink(missing_ok=True)

        return result
