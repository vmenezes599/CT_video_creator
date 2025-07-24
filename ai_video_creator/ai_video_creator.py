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
    
    # Create VideoCreator instance
    creator = VideoCreator(image_generator, audio_generator, video_generator)
    
    # Create video directly from JSON file
    creator.create_video_from_json(
        "input_data/new story/prompts/chapter_001.json",
        "chapter_001_video.mp4",
        "chapter_001_audio"
    )


def main_with_prompts():
    """
    Alternative main function that demonstrates loading prompts first.
    """
    # Load prompts from JSON file
    prompts = Prompt.load_from_json("input_data/new story/prompts/chapter_001.json")
    
    # Initialize generators
    image_generator = FluxAIImageGenerator()
    video_generator = VideoGenerator()
    audio_generator = ElevenLabsAudioGenerator()
    
    # Create VideoCreator instance
    creator = VideoCreator(image_generator, audio_generator, video_generator)
    
    # Create video from loaded prompts
    creator.create_video_from_prompts(prompts, "chapter_001_video.mp4", "chapter_001_audio")


def create_single_scene_video():
    """
    Example function for creating a video from a single prompt.
    """
    # Create a single prompt
    single_prompt = Prompt(
        narrator="This is a test narration for a single scene.",
        visual_description="A beautiful sunset over mountains with a peaceful lake.",
        visual_prompt="sunset, mountains, lake, peaceful, golden hour, cinematic"
    )
    
    # Initialize generators
    image_generator = FluxAIImageGenerator()
    video_generator = VideoGenerator()
    audio_generator = ElevenLabsAudioGenerator()
    
    # Create VideoCreator instance
    creator = VideoCreator(image_generator, audio_generator, video_generator)
    
    # Create video from single prompt
    creator.create_video_from_single_prompt(single_prompt, "single_scene.mp4")


def generate_video_from_story(story: list[Prompt]) -> None:
    """
    Generate a video from a story using AI-generated images and audio.

    Input:
        story (list[Prompt]): A list of Prompt objects containing narrator text,
            visual descriptions, and visual prompts for AI generation.
    """
    ai_image_generator = FluxAIImageGenerator()
    video_generator = VideoGenerator()
    # audio_generator = Pyttsx3AudioGenerator()
    audio_generator = ElevenLabsAudioGenerator()
    # audio_generator = SparkTTSComfyUIAudioGenerator()

    output_ai_image_generator: list[str] = []
    output_audio_generator: list[str] = []

    video_prompt_list: list[str] = []
    audio_prompt_list: list[str] = []
    audio_output_file_name = "output_audio"
    
    for prompt in story:
        # Use narrator text for audio generation
        audio_prompt_list.append(prompt.narrator)
        # Use visual_prompt for image generation (more specific than visual_description)
        video_prompt_list.append(prompt.visual_prompt)

    output_audio_generator = audio_generator.text_to_audio(
        audio_prompt_list, audio_output_file_name
    )
    output_ai_image_generator = ai_image_generator.generate_images(video_prompt_list)

    _output_ai_image_generator = [
        f"{COMFYUI_OUTPUT_FOLDER}/output_00001_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00002_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00003_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00004_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00005_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00006_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00007_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00008_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00009_.png",
        f"{COMFYUI_OUTPUT_FOLDER}/output_00010_.png",
    ]

    _output_audio_generator = [
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00001_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00002_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00003_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00004_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00005_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00006_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00007_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00008_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00009_.flac",
        f"{COMFYUI_OUTPUT_FOLDER}/output_audio_00010_.flac",
    ]

    video_generator.add_all_scenes(
        # [output_ai_image_generator[0]], [output_audio_generator[0]]
        output_ai_image_generator,
        output_audio_generator,
    )

    video_generator.compose("output_video.mp4")


if __name__ == "__main__":
    main()
