"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from .video_creator import VideoCreator


def main():
    """Main function to run the AI Video Creator application."""
    story_path = Path("stories/story_example")
    video_prompt_path = story_path / "prompts" / "chapter_001.json"
    VideoCreator.create_video_from_prompt(story_path, video_prompt_path)


if __name__ == "__main__":
    main()
