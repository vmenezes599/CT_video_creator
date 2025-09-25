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

    media_path: Path | None
    color_match_media_path: Path | None
    prompt: str
    seed: int
    recipe_type = "VideoRecipeBase"

    def __init__(
        self,
        media_path: Path | None,
        color_match_media_path: Path | None,
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

    def _clean_and_move_generated_files(
        self, output_file_path: Path, output_file_names: list[str]
    ) -> list[Path]:
        moved_files = []
        for file in output_file_names:
            file_path = Path(file)
            if file_path.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                moved_file = self._move_asset_to_output_path(
                    output_file_path.parent, file_path
                )
                if moved_file:
                    moved_files.append(moved_file)
            else:
                logger.debug(f"Removing extra generated file: {file_path}")
                try:
                    file_path.unlink()
                except OSError as e:
                    logger.warning(f"Failed to delete file {file_path}: {e}")

        return moved_files

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

        for lora, strength in zip(recipe.high_lora, recipe.high_lora_strength):
            workflow.add_high_lora(lora, strength)

        for lora, strength in zip(recipe.low_lora, recipe.low_lora_strength):
            workflow.add_low_lora(lora, strength)

        workflow.set_seed(recipe.seed)
        output_file_names = self.requests.comfyui_ensure_send_all_prompts([workflow])

        moved_files = self._clean_and_move_generated_files(
            output_file_path, output_file_names
        )

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

        for lora, strength in zip(recipe.high_lora, recipe.high_lora_strength):
            workflow.add_high_lora(lora, strength)

        for lora, strength in zip(recipe.low_lora, recipe.low_lora_strength):
            workflow.add_low_lora(lora, strength)

        workflow.set_seed(recipe.seed)

        output_file_names = self.requests.comfyui_ensure_send_all_prompts([workflow])

        delete_media_from_comfyui_input_folder(new_color_match_media_path)

        moved_files = self._clean_and_move_generated_files(
            output_file_path, output_file_names
        )

        return moved_files[0]


class WanVideoRecipe(VideoRecipeBase):
    """Video recipe for creating videos from stories."""

    COMPATIBLE_LORAS = [
        "NSFW-22-H-e8.safetensors",
        "NSFW-22-L-e8.safetensors",
        "Wan2.2-Fun-A14B-InP-high-noise-HPS2.1.safetensors",
        "Wan2.2-Fun-A14B-InP-high-noise-MPS.safetensors",
        "Wan2.2-Fun-A14B-InP-low-noise-HPS2.1.safetensors",
    ]

    GENERATOR = WanGenerator

    high_lora: list[str]
    high_lora_strength: list[float]
    low_lora: list[str]
    low_lora_strength: list[float]
    recipe_type = "WanVideoRecipeType"

    # Lists are dangerous default values because they are shared between instances
    # Thats why I use this _DEFAULT to fix this
    _DEFAULT = object()

    def __init__(
        self,
        prompt: str,
        color_match_media_path: str | None,
        high_lora: list[str] | None = _DEFAULT,
        high_lora_strength: list[float] | None = None,
        low_lora: list[str] | None = _DEFAULT,
        low_lora_strength: list[float] | None = None,
        media_path: str | None = None,
        seed: int | None = None,
    ):
        """Initialize WanVideoRecipe with media data.

        Args:
            prompt: Text prompt for media generation
            color_match_media_path: Path to the color match media file
            high_lora: List of high LORA models to apply
            high_lora_strength: List of strengths for each high LORA model
            low_lora: List of low LORA models to apply
            low_lora_strength: List of strengths for each low LORA model
            media_path: Path to the media file
            seed: Seed used for media generation
        """
        super().__init__(
            color_match_media_path=(
                Path(color_match_media_path) if color_match_media_path else None
            ),
            prompt=prompt,
            media_path=Path(media_path) if media_path else None,
            seed=random.randint(0, 2**64 - 1) if seed is None else seed,
            recipe_type=self.recipe_type,
        )
        if high_lora == self._DEFAULT:
            self.high_lora = ["Wan2.2-Fun-A14B-InP-high-noise-MPS.safetensors"]
        else:
            self.high_lora = high_lora if high_lora else []

        self.high_lora_strength = high_lora_strength if high_lora_strength else []

        # Ensure high_lora and high_lora_strength have the same length
        # high_lora is the main one, adjust high_lora_strength to match its length
        if len(self.high_lora_strength) < len(self.high_lora):
            # Extend with default value 1.0 if shorter
            self.high_lora_strength.extend(
                [1.0] * (len(self.high_lora) - len(self.high_lora_strength))
            )
        elif len(self.high_lora_strength) > len(self.high_lora):
            # Clip if longer
            self.high_lora_strength = self.high_lora_strength[: len(self.high_lora)]

        if low_lora == self._DEFAULT:
            self.low_lora = ["Wan2.2-Fun-A14B-InP-low-noise-HPS2.1.safetensors"]
        else:
            self.low_lora = low_lora if low_lora else []

        self.low_lora_strength = low_lora_strength if low_lora_strength else []

        # Ensure low_lora and low_lora_strength have the same length
        # low_lora is the main one, adjust low_lora_strength to match its length
        if len(self.low_lora_strength) < len(self.low_lora):
            # Extend with default value 1.0 if shorter
            self.low_lora_strength.extend(
                [1.0] * (len(self.low_lora) - len(self.low_lora_strength))
            )
        elif len(self.low_lora_strength) > len(self.low_lora):
            # Clip if longer
            self.low_lora_strength = self.low_lora_strength[: len(self.low_lora)]

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        # TODO: Remove this when web UI is mature?
        requests = ComfyUIRequests()
        comfyui_available_loras = requests.comfyui_get_available_loras()

        # Filter to only include LoRAs that are both in ComfyUI and in COMPATIBLE_LORAS
        available_loras = [
            lora for lora in self.COMPATIBLE_LORAS if lora in comfyui_available_loras
        ]

        return {
            "media_path": str(self.media_path) if self.media_path else None,
            "color_match_media_path": str(self.color_match_media_path),
            "prompt": self.prompt,
            "high_lora": [str(lora) for lora in self.high_lora],
            "high_lora_strength": [strength for strength in self.high_lora_strength],
            "low_lora": [str(lora) for lora in self.low_lora],
            "low_lora_strength": [strength for strength in self.low_lora_strength],
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
            color_match_media_path=data["color_match_media_path"],
            prompt=data["prompt"],
            media_path=data["media_path"],
            high_lora=data.get("high_lora", None),
            high_lora_strength=data.get("high_lora_strength", None),
            low_lora=data.get("low_lora", None),
            low_lora_strength=data.get("low_lora_strength", None),
            seed=data.get("seed", None),
        )
