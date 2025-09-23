"""
Path management for video recipe creation.
"""

from pathlib import Path


class VideoCreatorPaths:
    """Handles path management for video recipe creation."""

    def __init__(self, story_folder: Path, chapter_prompt_index: int):
        """Initialize VideoRecipePaths with story folder and chapter prompt path.

        Args:
            story_folder: Path to the story folder
            chapter_prompt_path: Path to the chapter prompt file
        """
        self.story_folder = story_folder

        # Initialize paths
        self.video_folder = self.story_folder / "video"
        self.chapter_folder = self.video_folder / f"chapter_{chapter_prompt_index:03}"
        self.asset_folder = self.chapter_folder / "assets"

        # Final paths
        self.narrator_and_image_asset_folder = self.asset_folder / "narrator_and_image"
        self.videos_asset_folder = self.asset_folder / "sub_videos"

        # Create directories if they don't exist
        self.narrator_and_image_asset_folder.mkdir(parents=True, exist_ok=True)
        self.videos_asset_folder.mkdir(parents=True, exist_ok=True)

        # Recipe file path
        self.narrator_and_image_recipe_file = (
            self.video_folder / "narrator_and_image_recipe.json"
        )
        self.narrator_and_image_asset_file = (
            self.video_folder / "narrator_and_image_assets.json"
        )
        self.video_recipe_file = self.video_folder / "sub_video_recipe.json"
        self.video_asset_file = self.video_folder / "sub_video_assets.json"
        self.video_effects_file = self.video_folder / "video_effects.json"
        self.video_output_file = self.video_folder / "output.mp4"
