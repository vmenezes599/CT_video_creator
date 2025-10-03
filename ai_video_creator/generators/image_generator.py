"""
AI Video Generation Module
"""

import random
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from logging_utils import logger

from ai_video_creator.ComfyUI_automation import ComfyUIRequests
from .ComfyUI_automation.comfyui_image_workflows import FluxWorkflow


class ImageRecipeBase:
    """Base class for image recipes."""

    prompt: str
    lora: str
    batch_size: int
    seed: int
    recipe_type = "ImageRecipeBase"

    def __init__(
        self, prompt: str, lora: str, seed: int, batch_size: int, recipe_type: str
    ):
        """Initialize ImageRecipeBase with a name."""
        self.prompt = prompt
        self.lora = lora
        self.seed = seed
        self.batch_size = batch_size
        self.recipe_type = recipe_type


class IImageGenerator(ABC):
    """Interface for image generators."""

    @abstractmethod
    def text_to_image(self, recipe: ImageRecipeBase, output_file_path: Path) -> Path:
        """Generate an image based on the recipe."""


class FluxAIImageGenerator(IImageGenerator):
    """
    A class to generate images based on a list of strings using ComfyUI workflows.
    """

    def __init__(self):
        """
        Initialize the AIImageGenerator class.
        """
        self.requests = ComfyUIRequests()  # Initialize ComfyUI requests

    def _move_asset_to_output_path(self, target_path: Path, asset_path: Path) -> Path:
        """Move asset to the database folder and return the new path."""
        if not asset_path.exists():
            logger.error(f"Asset file does not exist: {asset_path}")
            raise FileNotFoundError(f"Asset file does not exist: {asset_path}")

        complete_target_path = target_path / asset_path.name
        shutil.move(asset_path, complete_target_path)
        logger.trace(f"Asset moved successfully to: {complete_target_path}")
        return complete_target_path

    def text_to_image(self, recipe: "FluxImageRecipe", output_file_path: Path) -> Path:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """

        # Set the positive prompt in the workflow
        workflow = FluxWorkflow()

        workflow.set_positive_prompt(recipe.prompt)
        workflow.set_output_filename(output_file_path.stem)

        workflow.set_lora(recipe.lora)
        workflow.set_batch_size(recipe.batch_size)
        workflow.set_seed(recipe.seed)

        output_file_names = self.requests.comfyui_ensure_send_all_prompts([workflow])

        moved_files = [
            self._move_asset_to_output_path(output_file_path.parent, Path(file))
            for file in output_file_names
        ]

        return moved_files


class FluxImageRecipe(ImageRecipeBase):
    """Image recipe for creating images from stories."""

    GENERATOR = FluxAIImageGenerator
    LORA_SUBFOLDER = ["Flux"]

    recipe_type = "FluxImageRecipeType"

    def __init__(
        self,
        prompt: str,
        lora: str | None = None,
        batch_size: int | None = None,
        seed: int | None = None,
    ):
        """Initialize ImageRecipe with image data.

        Args:
            image_path: Path to the image file
            seed: Seed used for image generation
        """
        super().__init__(
            prompt=prompt,
            recipe_type=self.recipe_type,
            lora=lora if lora is not None else "",
            batch_size=batch_size if batch_size is not None else 1,
            seed=random.randint(0, 2**64 - 1) if seed is None else seed,
        )

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        requests = ComfyUIRequests()
        comfyui_available_loras = [
            Path(lora) for lora in requests.comfyui_get_available_loras()
        ]

        available_loras = []
        for lora in comfyui_available_loras:
            lora_folder = lora.parent.name
            if lora_folder in self.LORA_SUBFOLDER:
                available_loras.append(str(lora))

        return {
            "prompt": self.prompt,
            "lora": self.lora,
            "available_loras": available_loras,
            "batch_size": self.batch_size,
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
        required_keys = ["prompt", "recipe_type"]
        missing_fields = set(required_keys) - data.keys()
        for field in missing_fields:
            raise KeyError(f"Missing required key: {field}")

        if not isinstance(data["prompt"], str):
            raise ValueError("prompt must be a string")

        if cls.recipe_type != data["recipe_type"]:
            raise ValueError(f"Invalid recipe type: {cls.recipe_type}")

        return cls(
            prompt=data["prompt"],
            lora=data.get("lora", None),
            batch_size=data.get("batch_size", None),
            seed=data.get("seed", None),
        )
