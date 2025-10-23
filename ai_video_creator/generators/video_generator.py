"""
AI Video Generation Module
"""

import random
import tempfile

from abc import ABC, abstractmethod
from pathlib import Path
from typing_extensions import override
from logging_utils import logger

from ai_video_creator.ComfyUI_automation import ComfyUIRequests
from ai_video_creator.utils import safe_move, extract_video_last_frame

from .ComfyUI_automation.comfyui_video_workflows import (
    WanI2VWorkflow,
    WanT2VWorkflow,
)


class VideoRecipeBase:
    """Base class for video recipes."""

    prompt: str
    seed: int
    recipe_type = "VideoRecipeBase"

    def __init__(
        self,
        prompt: str,
        seed: int,
        recipe_type: str,
    ):
        """Initialize VideoRecipeBase with a name."""
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
    def generate_video(self, recipe: VideoRecipeBase, output_file_path: Path) -> Path:
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
    def generate_video(self, recipe: "WanRecipeBase", output_file_path: Path) -> Path:
        """
        Generate a video based on the recipe.
        """
        result = None

        if recipe.recipe_type == "WanT2VRecipeType":
            result = self.text_to_video(recipe, output_file_path)
        elif recipe.recipe_type == "WanI2VRecipeType":
            result = self.image_to_video(recipe, output_file_path)

        return result

    def _upload_media_to_comfyui(self, media_path: Path | str) -> Path:
        media_path = Path(media_path)
        with tempfile.TemporaryDirectory() as temp_folder:
            if media_path.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                media_path = extract_video_last_frame(media_path, temp_folder)

            return self.requests.upload_file(media_path)

    def _copy_color_match_media_to_comfyui_input_folder(
        self, media_path: Path | str
    ) -> Path | None:
        media_path = Path(media_path)
        if media_path.exists() and media_path.is_file():
            return self.requests.upload_file(media_path)
        return None

    def image_to_video(self, recipe: "WanI2VRecipe", output_file_path: Path) -> Path:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """

        new_media_path = self._upload_media_to_comfyui(recipe.media_path)

        new_color_match_media_path = (
            self._copy_color_match_media_to_comfyui_input_folder(
                recipe.color_match_media_path
            )
        )

        workflow = WanI2VWorkflow()

        workflow.set_positive_prompt(recipe.prompt)
        workflow.set_output_filename(output_file_path.stem)
        workflow.set_image_path(new_media_path.name)
        workflow.set_color_match_filename(
            new_color_match_media_path.name if new_color_match_media_path else None
        )

        for lora, strength in zip(recipe.high_lora, recipe.high_lora_strength):
            workflow.add_high_lora(lora, strength)

        for lora, strength in zip(recipe.low_lora, recipe.low_lora_strength):
            workflow.add_low_lora(lora, strength)

        workflow.set_seed(recipe.seed)
        result_files = self.requests.ensure_send_all_prompts(
            [workflow], output_file_path.parent
        )

        return result_files[0] if result_files else None

    def text_to_video(self, recipe: "WanT2VRecipe", output_file_path: Path) -> Path:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """

        color_match_media_path = Path(recipe.color_match_media_path)
        new_color_match_media_path = (
            self.requests.upload_file(recipe.color_match_media_path)
            if color_match_media_path.exists() and color_match_media_path.is_file()
            else None
        )

        workflow = WanT2VWorkflow()

        workflow.set_positive_prompt(recipe.prompt)
        workflow.set_output_filename(output_file_path.stem)

        for lora, strength in zip(recipe.high_lora, recipe.high_lora_strength):
            workflow.add_high_lora(lora, strength)

        for lora, strength in zip(recipe.low_lora, recipe.low_lora_strength):
            workflow.add_low_lora(lora, strength)

        workflow.set_seed(recipe.seed)

        result_files = self.requests.ensure_send_all_prompts(
            [workflow], output_file_path.parent
        )

        return result_files[0] if result_files else None


class WanRecipeBase(VideoRecipeBase):
    """Video recipe for creating videos from stories."""

    GENERATOR_TYPE = WanGenerator
    LORA_SUBFOLDER = ["Wan2.2_General"]

    color_media_path: str
    high_lora: list[str]
    high_lora_strength: list[float]
    low_lora: list[str]
    low_lora_strength: list[float]
    recipe_type = "WanRecipeBase"

    # Lists are dangerous default values because they are shared between instances
    # Thats why I use this _DEFAULT to fix this
    _DEFAULT = object()

    def __init__(
        self,
        prompt: str | None,
        color_match_media_path: str | None,
        high_lora: list[str] | None = _DEFAULT,
        high_lora_strength: list[float] | None = None,
        low_lora: list[str] | None = _DEFAULT,
        low_lora_strength: list[float] | None = None,
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
            prompt=prompt if prompt else "",
            seed=random.randint(0, 2**64 - 1) if seed is None else seed,
            recipe_type=self.recipe_type,
        )
        requests = ComfyUIRequests()
        available_loras = requests.get_available_loras()

        self.color_match_media_path = (
            color_match_media_path if color_match_media_path else ""
        )
        if high_lora is None or high_lora == self._DEFAULT:
            self.high_lora = [
                "Wan2.2_General/Wan2.2-Fun-A14B-InP-high-noise-MPS.safetensors"
            ]
        else:
            self.high_lora = (
                [lora for lora in high_lora if lora in available_loras]
                if high_lora
                else []
            )

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

        if low_lora is None or low_lora == self._DEFAULT:
            self.low_lora = [
                "Wan2.2_General/Wan2.2-Fun-A14B-InP-low-noise-HPS2.1.safetensors"
            ]
        else:
            self.low_lora = (
                [lora for lora in low_lora if lora in available_loras]
                if low_lora
                else []
            )

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

        # Initialize instance-specific lora subfolder with just the base class folders
        self.lora_subfolder = self.LORA_SUBFOLDER.copy()

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        # TODO: Remove this when web UI is mature?
        requests = ComfyUIRequests()
        comfyui_available_loras = [
            Path(lora) for lora in requests.get_available_loras()
        ]

        available_loras = []
        for lora in comfyui_available_loras:
            lora_folder = lora.parent.name
            if lora_folder in self.lora_subfolder:
                available_loras.append(str(lora))

        return {
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
    def from_dict(cls, data: dict) -> "WanRecipeBase":
        """Create WanRecipeBase from dictionary.

        Args:
            data: Dictionary containing WanRecipeBase data

        Returns:
            WanRecipeBase instance

        Raises:
            KeyError: If required keys are missing from data
            ValueError: If data format is invalid
        """
        # Validate required keys
        required_keys = [
            "color_match_media_path",
            "prompt",
            "recipe_type",
        ]
        missing_fields = set(required_keys) - data.keys()
        for field in missing_fields:
            raise KeyError(f"Missing required key: {field}")

        if data["color_match_media_path"] is not None and not isinstance(
            data["color_match_media_path"], str
        ):
            raise ValueError("color_match_media_path must be a string")

        if not isinstance(data["prompt"], str):
            raise ValueError("prompt must be a string")

        if cls.recipe_type != data["recipe_type"]:
            raise ValueError(f"Invalid recipe type: {cls.recipe_type}")

        return cls(
            color_match_media_path=data["color_match_media_path"],
            prompt=data["prompt"],
            high_lora=data.get("high_lora", None),
            high_lora_strength=data.get("high_lora_strength", None),
            low_lora=data.get("low_lora", None),
            low_lora_strength=data.get("low_lora_strength", None),
            seed=data.get("seed", None),
        )


class WanI2VRecipe(WanRecipeBase):
    """Video recipe for creating videos from stories."""

    LORA_SUBFOLDER = ["Wan2.2_I2V"]

    media_path: str
    recipe_type = "WanI2VRecipeType"

    def __init__(
        self,
        prompt: str | None,
        color_match_media_path: str | None,
        high_lora: list[str] | None = WanRecipeBase._DEFAULT,
        high_lora_strength: list[float] | None = None,
        low_lora: list[str] | None = WanRecipeBase._DEFAULT,
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
            prompt=prompt,
            color_match_media_path=color_match_media_path,
            high_lora=high_lora,
            high_lora_strength=high_lora_strength,
            low_lora=low_lora,
            low_lora_strength=low_lora_strength,
            seed=seed,
        )
        self.media_path = media_path if media_path else ""
        self.lora_subfolder = super().LORA_SUBFOLDER + self.LORA_SUBFOLDER

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        result = super().to_dict()
        result = {
            "media_path": str(self.media_path) if self.media_path else None,
            **result,
        }
        result.update({"recipe_type": self.recipe_type})
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "WanI2VRecipe":
        """Create WanI2VRecipe from dictionary.

        Args:
            data: Dictionary containing WanI2VRecipe data

        Returns:
            WanI2VRecipe instance

        Raises:
            KeyError: If required keys are missing from data
            ValueError: If data format is invalid
        """
        # Validate media_path field specific to this class
        if "media_path" not in data:
            raise KeyError("Missing required key: media_path")

        if data["media_path"] is not None and not isinstance(data["media_path"], str):
            raise ValueError("media_path must be a string")

        # Create base instance using parent's from_dict
        base_instance = super().from_dict(data)

        # Create new instance with our additional media_path field
        return cls(
            color_match_media_path=base_instance.color_match_media_path,
            prompt=base_instance.prompt,
            media_path=data["media_path"],
            high_lora=base_instance.high_lora,
            high_lora_strength=base_instance.high_lora_strength,
            low_lora=base_instance.low_lora,
            low_lora_strength=base_instance.low_lora_strength,
            seed=base_instance.seed,
        )


# TODO: Change subclass to WanRecipeBase. This is to simplify the manual recipe editing.
class WanT2VRecipe(WanI2VRecipe):
    """Video recipe for creating videos from stories."""

    LORA_SUBFOLDER = ["Wan2.2_T2V"]
    recipe_type = "WanT2VRecipeType"

    def __init__(
        self,
        prompt: str | None,
        color_match_media_path: str | None,
        high_lora: list[str] | None = WanRecipeBase._DEFAULT,
        high_lora_strength: list[float] | None = None,
        low_lora: list[str] | None = WanRecipeBase._DEFAULT,
        low_lora_strength: list[float] | None = None,
        # TODO: Remove media_path when changing subclass to WanRecipeBase
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
            prompt=prompt,
            color_match_media_path=color_match_media_path,
            high_lora=high_lora,
            high_lora_strength=high_lora_strength,
            low_lora=low_lora,
            low_lora_strength=low_lora_strength,
            media_path=media_path,
            seed=seed,
        )
        # Create instance-specific LORA_SUBFOLDER combining parent and child
        self.lora_subfolder = super().LORA_SUBFOLDER + self.LORA_SUBFOLDER

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        result = super().to_dict()
        result.update({"recipe_type": self.recipe_type})
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "WanT2VRecipe":
        """Create WanT2VRecipe from dictionary.

        Args:
            data: Dictionary containing WanT2VRecipe data

        Returns:
            WanT2VRecipe instance

        Raises:
            KeyError: If required keys are missing from data
            ValueError: If data format is invalid
        """
        # WanT2VRecipe has no extra fields beyond WanRecipeBase, so just delegate
        return super().from_dict(data)
