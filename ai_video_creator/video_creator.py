"""
AI Video Generation Module
"""

import json
from pathlib import Path

from .video_assembler import VideoAssembler
from .video_recipe import VideoRecipeCreator
from .prompt import Prompt

from .generators import FluxAIImageGenerator


class VideoCreator:
    """A class to create videos from prompts using the VideoAssembler."""

    DEFAULT_IMAGE_GENERATOR = FluxAIImageGenerator

    @classmethod
    def create_video_from_prompt(
        cls, story_path: Path, video_prompt_path: Path
    ) -> None:
        """
        Create a video from a video prompt file.

        Args:
            video_prompt_path: Path to the video prompt file.

        Returns:
            None
        """
        video_recipe_creator = VideoRecipeCreator(
            prompt_file=video_prompt_path,
            story_path=story_path,
        )
        video_recipe = video_recipe_creator.create_video_recipe()

        # Define output path and filename
        output_path = Path("output_videos")
        output_path.mkdir(parents=True, exist_ok=True)
        output_filename = "generated_video"

        # Create the video
        video_creator = VideoAssembler()
        video_creator.create_video_from_recipe(
            video_recipe, output_path, output_filename
        )
