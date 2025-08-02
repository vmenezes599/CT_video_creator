"""
AI Video Generation Module
"""

from pathlib import Path
import random
from ai_video_creator.ComfyUI_automation.comfyui_requests import ComfyUIRequests
from abc import ABC, abstractmethod

from .ComfyUI_automation.comfyui_image_workflows import FluxWorkflow


class ImageRecipeBase:
    """Base class for image recipes."""

    prompt: str
    seed: int
    recipe_type = "ImageRecipeBase"

    def __init__(self, prompt: str, seed: int, recipe_type: str):
        """Initialize ImageRecipeBase with a name."""
        self.recipe_type = recipe_type
        self.prompt = prompt
        if seed:
            self.seed = seed


class IImageGenerator(ABC):
    """Interface for image generators."""

    @abstractmethod
    def text_to_image(self, recipe: ImageRecipeBase, output_file_name: str) -> Path:
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

    def text_to_image(self, recipe: "FluxImageRecipe", output_file_name: str) -> Path:
        """
        Generate images for a list of prompts and return the paths to the generated images.

        :param prompts: A list of text prompts to generate images for.
        :return: A list of file paths to the generated images.
        """

        # Set the positive prompt in the workflow
        workflow = FluxWorkflow()

        workflow.set_positive_prompt(recipe.prompt)
        workflow.set_output_filename(output_file_name)

        workflow.set_seed(recipe.seed)

        output_file_names = self.requests.comfyui_ensure_send_all_prompts([workflow])

        return Path(output_file_names[0])


class FluxImageRecipe(ImageRecipeBase):
    """Image recipe for creating images from stories."""

    GENERATOR = FluxAIImageGenerator

    recipe_type = "FluxImageRecipeType"

    def __init__(self, prompt: str, seed: int | None = None):
        """Initialize ImageRecipe with image data.

        Args:
            image_path: Path to the image file
            seed: Seed used for image generation
        """
        super().__init__(
            prompt=prompt,
            recipe_type=self.recipe_type,
            seed=random.randint(0, 2**64 - 1) if seed is None else seed,
        )

    def to_dict(self) -> dict:
        """Convert ImageRecipe to dictionary.

        Returns:
            Dictionary representation of the ImageRecipe
        """
        return {
            "prompt": self.prompt,
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
        required_keys = ["prompt", "recipe_type", "seed"]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required key: {key}")

        if not isinstance(data["prompt"], str):
            raise ValueError("prompt must be a string")
        if not isinstance(data["seed"], int):
            raise ValueError("seed must be an integer")

        if cls.recipe_type != data["recipe_type"]:
            raise ValueError(f"Invalid recipe type: {cls.recipe_type}")

        return cls(
            prompt=data["prompt"],
            seed=data["seed"],
        )
