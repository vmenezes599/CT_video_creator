"""This module is the main entry point for the AI Video Creator application."""

from pathlib import Path
from .video_creator import create_chapter_video_recipe, assemble_chapter_video


def main():
    """Main function to run the AI Video Creator application."""
    story_path = Path("stories/The retainer")
    chapter_index = 0

    create_chapter_video_recipe(story_path, chapter_index=chapter_index)
    assemble_chapter_video(story_path, chapter_index=chapter_index)


if __name__ == "__main__":
    main()
