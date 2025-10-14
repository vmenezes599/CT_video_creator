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

        self.chapter_prompt_path = (
            story_folder / "prompts" / f"chapter_{chapter_prompt_index+1:03}.json"
        )

        # Initialize paths
        self.video_folder = self.story_folder / "video"
        self.video_chapter_folder = (
            self.video_folder / f"chapter_{chapter_prompt_index+1:03}"
        )
        self.asset_folder = self.video_chapter_folder / "assets"

        # Final modules paths
        self.narrator_asset_folder = self.asset_folder / "narrators"
        self.image_asset_folder = self.asset_folder / "images"
        self.sub_videos_asset_folder = self.asset_folder / "sub_videos"
        self.video_assembler_asset_folder = self.asset_folder / "video_assembler"

        # Create directories if they don't exist
        self.narrator_asset_folder.mkdir(parents=True, exist_ok=True)
        self.image_asset_folder.mkdir(parents=True, exist_ok=True)
        self.sub_videos_asset_folder.mkdir(parents=True, exist_ok=True)
        self.video_assembler_asset_folder.mkdir(parents=True, exist_ok=True)

        # Recipe file paths
        self.narrator_recipe_file = self.video_chapter_folder / "narrator_recipe.json"
        self.narrator_asset_file = self.video_chapter_folder / "narrator_assets.json"
        self.image_recipe_file = self.video_chapter_folder / "image_recipe.json"
        self.image_asset_file = self.video_chapter_folder / "image_assets.json"

        self.sub_video_recipe_file = self.video_chapter_folder / "sub_video_recipe.json"
        self.sub_video_asset_file = self.video_chapter_folder / "sub_video_assets.json"
        self.video_assembler_asset_file = (
            self.video_chapter_folder / "video_assembler_assets.json"
        )
        self.video_effects_file = self.video_chapter_folder / "video_effects.json"
        self.video_output_file = self.video_chapter_folder / "output.mp4"
