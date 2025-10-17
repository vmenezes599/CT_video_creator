"""
Fake implementations for testing AI Video Creator without overmocking.

These fake implementations create real files and exercise actual business logic
while avoiding external dependencies like ComfyUI, TTS servers, etc.
"""

from pathlib import Path
from typing import List

from ai_video_creator.generators import (
    IAudioGenerator,
    IImageGenerator,
    IVideoGenerator,
    AudioRecipeBase,
    ImageRecipeBase,
    VideoRecipeBase,
)


class FakeAudioGenerator(IAudioGenerator):
    """Fake audio generator that creates real files for testing."""

    def __init__(self, track_calls: bool = False):
        """Initialize with optional call tracking."""
        self.track_calls = track_calls
        self.calls = []

    def clone_text_to_speech(
        self, recipe: AudioRecipeBase, output_file_path: Path
    ) -> Path:
        """Create a fake audio file with recipe content."""
        if self.track_calls:
            self.calls.append(f"audio: {recipe.prompt}")

        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file_path.write_text(
            f"Fake audio content for: {recipe.prompt}\n"
            f"Recipe type: {recipe.recipe_type}\n"
            f"Generated at: {output_file_path}"
        )
        return output_file_path

    def text_to_speech(self, text_list: List[str], output_file_path: Path) -> Path:
        """Create fake audio from text list."""
        if self.track_calls:
            self.calls.append(f"text_to_speech: {len(text_list)} items")

        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file_path.write_text(f"Fake audio for texts: {', '.join(text_list)}")
        return output_file_path

    def play(self, text: str) -> None:
        """Mock play functionality."""
        if self.track_calls:
            self.calls.append(f"play: {text}")


class FakeImageGenerator(IImageGenerator):
    """Fake image generator that creates real files for testing."""

    def __init__(self, track_calls: bool = False):
        """Initialize with optional call tracking."""
        self.track_calls = track_calls
        self.calls = []

    def text_to_image(
        self, recipe: ImageRecipeBase, output_file_path: Path
    ) -> List[Path]:
        """Create a fake image file with recipe content."""
        if self.track_calls:
            self.calls.append(f"image: {recipe.prompt}")

        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file_path.write_text(
            f"Fake image content for: {recipe.prompt}\n"
            f"Recipe type: {recipe.recipe_type}\n"
            f"Seed: {getattr(recipe, 'seed', 'N/A')}\n"
            f"Generated at: {output_file_path}"
        )
        return [output_file_path]


class FakeVideoGenerator(IVideoGenerator):
    """Fake video generator that creates real files for testing."""

    def __init__(self, track_calls: bool = False):
        """Initialize with optional call tracking."""
        self.track_calls = track_calls
        self.calls = []

    def generate_video(self, recipe: VideoRecipeBase, output_file_path: Path) -> Path:
        """Create a fake video file with recipe content."""
        if self.track_calls:
            self.calls.append(f"video: {recipe.prompt}")

        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        output_file_path.write_text(
            f"Fake video content for: {recipe.prompt}\n"
            f"Recipe type: {recipe.recipe_type}\n"
            f"Media path: {getattr(recipe, 'media_path', 'N/A')}\n"
            f"Generated at: {output_file_path}"
        )
        return output_file_path


class TrackingFakeGenerators:
    """Utility class to track calls across multiple fake generators."""

    def __init__(self):
        """Initialize with shared call tracking."""
        self.calls = []
        self.audio_generator = FakeAudioGenerator(track_calls=True)
        self.image_generator = FakeImageGenerator(track_calls=True)
        self.video_generator = FakeVideoGenerator(track_calls=True)

        # Redirect calls to shared tracking
        self.audio_generator.calls = self.calls
        self.image_generator.calls = self.calls
        self.video_generator.calls = self.calls

    def get_audio_generator(self):
        """Get the fake audio generator."""
        return self.audio_generator

    def get_image_generator(self):
        """Get the fake image generator."""
        return self.image_generator

    def get_video_generator(self):
        """Get the fake video generator."""
        return self.video_generator

    def reset_calls(self):
        """Reset call tracking."""
        self.calls.clear()

    def get_call_count(self) -> int:
        """Get total number of generator calls."""
        return len(self.calls)

    def get_calls_by_type(self, call_type: str) -> List[str]:
        """Get calls filtered by type (audio, image, video)."""
        return [call for call in self.calls if call.startswith(call_type)]


def setup_fake_generators_for_recipes(recipes, generator_type="all"):
    """
    Helper function to replace generators in recipe objects with fake implementations.

    Args:
        recipes: List of recipe objects or nested lists
        generator_type: "audio", "image", "video", or "all"
    """

    def replace_generator(recipe_obj):
        if hasattr(recipe_obj, "GENERATOR_TYPE"):
            if generator_type in ["audio", "all"] and hasattr(
                recipe_obj, "clone_voice_path"
            ):
                recipe_obj.GENERATOR_TYPE = lambda: FakeAudioGenerator()
            elif (
                generator_type in ["image", "all"]
                and hasattr(recipe_obj, "prompt")
                and hasattr(recipe_obj, "seed")
            ):
                recipe_obj.GENERATOR_TYPE = lambda: FakeImageGenerator()
            elif generator_type in ["video", "all"] and hasattr(
                recipe_obj, "media_path"
            ):
                recipe_obj.GENERATOR_TYPE = lambda: FakeVideoGenerator()

    # Handle nested structures
    if isinstance(recipes, list):
        for item in recipes:
            if isinstance(item, list):
                for recipe in item:
                    replace_generator(recipe)
            else:
                replace_generator(item)
    else:
        replace_generator(recipes)
