"""
AI Video Generation Module
"""

from .audio.audio_generation import (
    Pyttsx3AudioGenerator,
    ElevenLabsAudioGenerator,
    SparkTTSComfyUIAudioGenerator,
)

from .video.ai_image_generator import FluxAIImageGenerator
from .video.video_generation import VideoGenerator
from .prompt.prompt import Prompt
from .video_creator import VideoCreator

from .environment_variables import COMFYUI_OUTPUT_FOLDER


def main():
    """
    Main function to generate a video from a story.
    """
    # Initialize generators
    image_generator = FluxAIImageGenerator()
    video_generator = VideoGenerator()
    audio_generator = SparkTTSComfyUIAudioGenerator()

    audio_generator.text_to_audio(["This is a test audio generation."], "testing.mp3")

    return

    # Create VideoCreator instance
    creator = VideoCreator(image_generator, audio_generator, video_generator)

    # Create video directly from JSON file
    creator.create_video_from_json(
        "input_data/new story/prompts/chapter_001.json",
        "chapter_001_video.mp4",
        "chapter_001_audio",
    )


if __name__ == "__main__":
    main()
