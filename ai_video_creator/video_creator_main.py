"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from .video_creator import create_chapter_video_recipe, assemble_chapter_video


def main():
    """Main function to run the AI Video Creator application."""
    story_path = Path("stories/story_example")
    video_prompt_path = story_path / "prompts" / "chapter_001.json"

    create_chapter_video_recipe(story_path, video_prompt_path)
    assemble_chapter_video(story_path, chapter_index=0)


if __name__ == "__main__":
    main()
