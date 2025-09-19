"""
AI Video Generation Module
"""

import copy
import random

from abc import ABC, abstractmethod
from pathlib import Path
from typing_extensions import override
from logging_utils import logger

from ai_video_creator.ComfyUI_automation import ComfyUIRequests
from ai_video_creator.ComfyUI_automation import (
    copy_media_to_comfyui_input_folder,
    delete_media_from_comfyui_input_folder,
)
from ai_video_creator.utils import safe_move

from .ComfyUI_automation.comfyui_video_workflows import WanI2VWorkflow, WanV2VWorkflow


class VideoRecipeBase:
    """Base class for video recipes."""

    media_path: Path
    prompt: str
    seed: int
    recipe_type = "VideoRecipeBase"

    def __init__(
        self,
        media_path: Path,
        color_match_media_path: Path,
        prompt: str,
        seed: int,
        recipe_type: str,
    ):
        """Initialize VideoRecipeBase with a name."""
        self.media_path = media_path
        self.color_match_media_path = color_match_media_path
        self.prompt = prompt
        self.seed = seed
        self.recipe_type = recipe_type


class IVideoGenerator(ABC):
    """Interface for video generators."""

    def _move_asset_to_output_path(self, target_path: Path, asset_path: Path) -> Path:
        """Move asset to the database folder and return the new path."""
        if not asset_path.exists():
            logger.warning(
                f"Asset file does not exist while trying to move it: {asset_path}"
            )
            logger.warning("Sometimes ComfyUI return temporary files. Ignoring...")
            return Path("")

        complete_target_path = target_path / asset_path.name
        complete_target_path = safe_move(asset_path, complete_target_path)
        logger.trace(f"Asset moved successfully to: {complete_target_path}")
        return complete_target_path

    @abstractmethod
    def media_to_video(self, recipe: VideoRecipeBase, output_file_path: Path) -> Path:
        """Generate a video based on the recipe."""


class WanGenerator(IVideoGenerator):
    """
    A class to generate videos based on a list of strings using ComfyUI workflows.
    """

    def __init__(self):
        """
        Initialize the WanGenerator class.
        :param generation_count: Number of passes of WAN. Each passes adds 5 second of video.
        """
        self.requests = ComfyUIRequests()  # Initialize ComfyUI requests

    @override
    def media_to_video(self, recipe: "WanVideoRecipe", output_file_path: Path) -> Path:
        """
        Generate a video based on the recipe.
        """

        new_media_path = copy_media_to_comfyui_input_folder(recipe.media_path)

        changed_recipe = copy.deepcopy(recipe)
        changed_recipe.media_path = Path(new_media_path.name)

        if changed_recipe.media_path.suffix.lower() in [
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".gif",
        ]:
            result = self.image_to_video(changed_recipe, output_file_path)
        elif changed_recipe.media_path.suffix.lower() in [
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
        ]:
            result = self.video_to_video(changed_recipe, output_file_path)
        else:
            logger.error(
                f"Unsupported media format: {recipe.media_path.suffix} for file {recipe.media_path}"
            )
            raise ValueError(
                f"Unsupported media format: {recipe.media_path.suffix} for file {recipe.media_path}"
            )

        delete_media_from_comfyui_input_folder(new_media_path)

        return result

    def image_to_video(self, recipe: "WanVideoRecipe", output_file_path: Path) -> Path:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """

        workflow = WanI2VWorkflow()

        workflow.set_positive_prompt(recipe.prompt)
        workflow.set_output_filename(output_file_path.stem)
        workflow.set_image_path(str(recipe.media_path))

        workflow.set_seed(recipe.seed)

        output_file_names = self.requests.comfyui_ensure_send_all_prompts([workflow])

        moved_files = [
            self._move_asset_to_output_path(output_file_path.parent, Path(file))
            for file in output_file_names
            if Path(file).suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]
        ]

        return moved_files[0]

    def video_to_video(self, recipe: "WanVideoRecipe", output_file_path: Path) -> Path:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """

        new_color_match_media_path = copy_media_to_comfyui_input_folder(
            recipe.color_match_media_path
        )

        workflow = WanV2VWorkflow()

        workflow.set_positive_prompt(recipe.prompt)
        workflow.set_output_filename(output_file_path.stem)
        workflow.set_color_match_filename(str(new_color_match_media_path.name))
        workflow.set_video_path(str(recipe.media_path))

        workflow.set_seed(recipe.seed)

        output_file_names = self.requests.comfyui_ensure_send_all_prompts([workflow])

        delete_media_from_comfyui_input_folder(new_color_match_media_path)

        moved_files = [
            self._move_asset_to_output_path(output_file_path.parent, Path(file))
            for file in output_file_names
            if Path(file).suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]
        ]

        return moved_files[0] if moved_files else Path("")


class WanVideoRecipe(VideoRecipeBase):
    """Video recipe for creating videos from stories."""

    GENERATOR = WanGenerator

    recipe_type = "WanVideoRecipeType"

    def __init__(
        self,
        prompt: str,
        color_match_media_path: str,
        media_path: str | None = None,
        seed: int | None = None,
    ):
        """Initialize WanVideoRecipe with media data.

        Args:
            prompt: Text prompt for media generation
            media_path: Path to the media file
            color_match_media_path: Path to the color match media file
            seed: Seed used for media generation
        """
        super().__init__(
            color_match_media_path=Path(color_match_media_path),
            prompt=prompt,
            media_path=Path(media_path) if media_path else None,
            seed=random.randint(0, 2**64 - 1) if seed is None else seed,
            recipe_type=self.recipe_type,
        )

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        # TODO: Remove this when web UI is mature?
        requests = ComfyUIRequests()
        available_loras = requests.comfyui_get_available_loras()

        return {
            "media_path": str(self.media_path) if self.media_path else None,
            "color_match_media_path": str(self.color_match_media_path),
            "prompt": self.prompt,
            "available_loras": available_loras,
            "seed": self.seed,
            "recipe_type": self.recipe_type,
        }

    @classmethod
    def from_dict(
        cls, data: dict
    ) -> "ImageRecipe":  # pyright: ignore[reportUndefinedVariable]
        """Create ImageRecipe from dictionary.

        Args:
            data: Dictionary containing ImageRecipe data

        Returns:
            ImageRecipe instance

        Raises:
            KeyError: If required keys are missing from data
            ValueError: If data format is invalid
        """
        # Validate required keys
        required_keys = [
            "media_path",
            "color_match_media_path",
            "prompt",
            "recipe_type",
        ]
        missing_fields = set(required_keys) - data.keys()
        for field in missing_fields:
            raise KeyError(f"Missing required key: {field}")

        if data["media_path"] is not None and not isinstance(data["media_path"], str):
            raise ValueError("media_path must be a string")

        if not isinstance(data["color_match_media_path"], str):
            raise ValueError("color_match_media_path must be a string")

        if not isinstance(data["prompt"], str):
            raise ValueError("prompt must be a string")

        if cls.recipe_type != data["recipe_type"]:
            raise ValueError(f"Invalid recipe type: {cls.recipe_type}")

        return cls(
            media_path=data["media_path"],
            color_match_media_path=data["color_match_media_path"],
            prompt=data["prompt"],
            seed=data.get("seed", None),
        )
