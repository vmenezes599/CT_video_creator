"""
AI Video Generation Module
"""

import random
from abc import ABC, abstractmethod
from pathlib import Path
from requests.exceptions import RequestException
from ct_logging import logger

from ct_video_creator.utils import safe_move
from ct_video_creator.comfyui import ComfyUIRequests, FluxWorkflow


class ImageRecipeBase:
    """Base class for image recipes."""

    prompt: str
    lora: str
    batch_size: int
    seed: int
    width: int
    height: int
    recipe_type = "ImageRecipeBase"

    def __init__(self, prompt: str, lora: str, seed: int, batch_size: int, width: int, height: int, recipe_type: str):
        """Initialize ImageRecipeBase with a name."""
        self.prompt = prompt
        self.lora = lora
        self.seed = seed
        self.batch_size = batch_size
        self.width = width
        self.height = height
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
        move_result = safe_move(asset_path, complete_target_path)
        logger.trace(f"Asset moved successfully to: {complete_target_path}")
        return move_result

    def text_to_image(self, recipe: ImageRecipeBase, output_file_path: Path) -> Path:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """
        if not isinstance(recipe, FluxImageRecipe):
            raise TypeError(f"Expected FluxImageRecipe, got {type(recipe).__name__}")

        # Set the positive prompt in the workflow
        workflow = FluxWorkflow()

        workflow.set_positive_prompt(recipe.prompt)
        workflow.set_output_filename(output_file_path.stem)

        workflow.set_image_resolution(recipe.width, recipe.height)
        workflow.set_lora(recipe.lora)
        workflow.set_batch_size(recipe.batch_size)
        workflow.set_seed(recipe.seed)

        result_files = self.requests.ensure_send_all_prompts([workflow], output_file_path.parent)

        if not result_files:
            raise RuntimeError("No image files were generated")
        
        return Path(result_files[0])


class FluxImageRecipe(ImageRecipeBase):
    """Image recipe for creating images from stories."""

    GENERATOR_TYPE = FluxAIImageGenerator
    LORA_SUBFOLDER = ["Flux"]

    recipe_type = "FluxImageRecipeType"

    def __init__(
        self,
        prompt: str,
        width: int,
        height: int,
        lora: str | None = None,
        batch_size: int | None = None,
        seed: int | None = None,
    ):
        """Initialize ImageRecipe with image data.

        Args:
            image_path: Path to the image file
            seed: Seed used for image generation
        """
        validated_lora = lora or ""

        batch_size = batch_size if batch_size is not None else 1
        seed = seed if seed is not None else random.randint(0, 2**31 - 1)

        super().__init__(
            prompt=prompt,
            recipe_type=self.recipe_type,
            lora=validated_lora,
            batch_size=batch_size,
            seed=seed,
            width=width,
            height=height,
        )

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        try:
            requests = ComfyUIRequests()
            comfyui_available_loras = [Path(lora) for lora in requests.get_available_loras()]
        except RequestException:
            logger.warning("Unable to fetch available LORAs for serialization; returning empty list.")
            comfyui_available_loras = []

        available_loras = []
        for lora in comfyui_available_loras:
            lora_folder = lora.parent.name
            if lora_folder in self.LORA_SUBFOLDER:
                available_loras.append(str(lora))

        return {
            "prompt": self.prompt,
            "lora": self.lora,
            "available_loras": available_loras,
            "width": self.width,
            "height": self.height,
            "batch_size": self.batch_size,
            "seed": self.seed,
            "recipe_type": self.recipe_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImageRecipe":  # pyright: ignore[reportUndefinedVariable]
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
            width=data["width"],
            height=data["height"],
            lora=data.get("lora", None),
            batch_size=data.get("batch_size", None),
            seed=data.get("seed", None),
        )
