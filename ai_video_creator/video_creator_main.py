"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from .video_creator import create_recipe_from_prompt, create_video_from_assets


def main():
    """Main function to run the AI Video Creator application."""
    story_path = Path("stories/The retainer")
    chapter_index = 0

    create_recipe_from_prompt(story_path, chapter_index=chapter_index)
    create_video_from_assets(story_path, chapter_index=chapter_index)


if __name__ == "__main__":
    main()
