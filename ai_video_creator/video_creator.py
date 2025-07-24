"""
Video Creator Module

This module contains the VideoCreator class that orchestrates the entire video creation process
by coordinating image generation, audio generation, and video composition.
"""

from typing import Protocol
from .prompt.prompt import Prompt


class ImageGeneratorProtocol(Protocol):
    """Protocol for image generators."""

    def text_to_image(self, prompts: list[str]) -> list[str]:
        """Generate images from text prompts."""
        pass


class AudioGeneratorProtocol(Protocol):
    """Protocol for audio generators."""

    def text_to_audio(self, prompts: list[str], output_file_name: str) -> list[str]:
        """Generate audio from text prompts."""
        pass


class VideoGeneratorProtocol(Protocol):
    """Protocol for video generators."""

    def add_all_scenes(self, image_paths: list[str], audio_paths: list[str]) -> None:
        """Add all scenes to the video."""
        pass

    def compose(self, output_filename: str) -> None:
        """Compose the final video."""
        pass


class VideoCreator:
    """
    A class that orchestrates the video creation process by coordinating
    image generation, audio generation, and video composition.
    """

    def __init__(
        self,
        image_generator: ImageGeneratorProtocol,
        audio_generator: AudioGeneratorProtocol,
        video_generator: VideoGeneratorProtocol,
    ):
        """
        Initialize VideoCreator with the required generators.

        Args:
            image_generator: Generator for creating images from text prompts
            audio_generator: Generator for creating audio from text prompts
            video_generator: Generator for composing final video
        """
        self.__image_generator = image_generator
        self.__audio_generator = audio_generator
        self.__video_generator = video_generator

    def create_video_from_prompts(
        self,
        prompts: list[Prompt],
        output_filename: str = "output_video.mp4",
        audio_output_name: str = "output_audio",
    ) -> None:
        """
        Create a video from a list of prompts.

        Args:
            prompts: List of Prompt objects containing narrator text and visual prompts
            output_filename: Name of the output video file
            audio_output_name: Base name for audio output files
        """
        if not prompts:
            raise ValueError("Prompts list cannot be empty")

        # Extract prompts for audio and image generation
        audio_prompts = [prompt.narrator for prompt in prompts]
        visual_prompts = [prompt.visual_prompt for prompt in prompts]

        # Generate audio and images
        audio_files = self.__audio_generator.text_to_audio(
            audio_prompts, audio_output_name
        )
        image_files = self.__image_generator.text_to_image(visual_prompts)

        # Compose the video
        self.__video_generator.add_all_scenes(image_files, audio_files)
        self.__video_generator.compose(output_filename)

    def create_video_from_single_prompt(
        self,
        prompt: Prompt,
        output_filename: str = "single_scene_video.mp4",
        audio_output_name: str = "single_audio",
    ) -> None:
        """
        Create a video from a single prompt.

        Args:
            prompt: Single Prompt object
            output_filename: Name of the output video file
            audio_output_name: Base name for audio output files
        """
        self.create_video_from_prompts([prompt], output_filename, audio_output_name)

    def create_video_from_json(
        self,
        json_file_path: str,
        output_filename: str = "story_video.mp4",
        audio_output_name: str = "story_audio",
    ) -> None:
        """
        Create a video directly from a JSON file containing prompts.

        Args:
            json_file_path: Path to the JSON file containing prompts
            output_filename: Name of the output video file
            audio_output_name: Base name for audio output files
        """
        prompts = Prompt.load_from_json(json_file_path)
        self.create_video_from_prompts(prompts, output_filename, audio_output_name)

    @property
    def image_generator(self) -> ImageGeneratorProtocol:
        """Get the image generator."""
        return self.__image_generator

    @property
    def audio_generator(self) -> AudioGeneratorProtocol:
        """Get the audio generator."""
        return self.__audio_generator

    @property
    def video_generator(self) -> VideoGeneratorProtocol:
        """Get the video generator."""
        return self.__video_generator
