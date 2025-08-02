"""
Path management for video recipe creation.
"""

from pathlib import Path


class VideoRecipePaths:
    """Handles path management for video recipe creation."""

    def __init__(self, story_folder: Path, chapter_prompt_path: Path):
        """Initialize VideoRecipePaths with story folder and chapter prompt path.

        Args:
            story_folder: Path to the story folder
            chapter_prompt_path: Path to the chapter prompt file
        """
        self.story_folder = story_folder
        self.chapter_prompt_path = chapter_prompt_path

        # Initialize paths
        self.video_path = story_folder / "video"
        self.assets_path = self.video_path / "assets"
        self.prompts_path = story_folder / "prompts"

        # Create directories if they don't exist
        self.assets_path.mkdir(parents=True, exist_ok=True)

        # Generate recipe name
        self.recipe_name = (
            f"{self.video_path.name}_{self.chapter_prompt_path.stem}_recipe"
        )

        # Recipe file path
        self.recipe_file = self.video_path / f"{self.recipe_name}.json"
        self.video_asset_file = (
            self.video_path / f"{self.recipe_name}_video_assets.json"
        )
        self.video_output_file = self.video_path / f"{self.recipe_name}_output.mp4"

    @classmethod
    def create_from_story_and_index(
        cls, story_folder: Path, chapter_prompt_index: int
    ) -> "VideoRecipePaths":
        """Create VideoRecipePaths from story folder and chapter index.

        Args:
            story_folder: Path to the story folder
            chapter_prompt_index: Index of the chapter prompt

        Returns:
            VideoRecipePaths instance

        Raises:
            ValueError: If no prompt found for the given index
        """
        chapter_prompt_path = cls._find_prompt_by_index(
            story_folder, chapter_prompt_index
        )
        return cls(story_folder, chapter_prompt_path)

    @staticmethod
    def _find_prompt_by_index(story_folder: Path, index: int) -> Path:
        """Find prompt by chapter index.

        Args:
            story_folder: Path to the story folder
            index: Chapter index

        Returns:
            Path to the prompt file

        Raises:
            ValueError: If no prompt found for the given index
        """
        # Adjust index to match file naming convention
        adjusted_index = index + 1

        prompts_path = story_folder / "prompts"
        if not prompts_path.exists():
            raise ValueError(f"Prompts folder does not exist: {prompts_path}")

        for prompt_file in prompts_path.iterdir():
            if (
                prompt_file.suffix == ".json"
                and prompt_file.stem.find(f"{adjusted_index:03}") != -1
            ):
                return prompt_file

        raise ValueError(
            f"No prompt found for chapter index {index} (adjusted: {adjusted_index})"
        )

    def get_audio_name(self, index: int) -> str:
        """Get audio file name for the given index.

        Args:
            index: Index of the audio item

        Returns:
            Audio file name
        """
        return f"{self.recipe_name}_narration_index{index}"

    def get_image_name(self, index: int) -> str:
        """Get image file name for the given index.

        Args:
            index: Index of the image item

        Returns:
            Image file name
        """
        return f"{self.recipe_name}_visual_index{index}"

    def move_assets_to_story_folder(self, asset_list: list[Path]) -> list[Path]:
        """Move generated assets to the story assets folder.

        Args:
            asset_list: List of asset paths to move

        Returns:
            List of new asset paths after moving
        """
        new_path_list = []
        for asset in asset_list:
            asset_current_path = Path(asset)
            if (
                asset_current_path.exists()
                and asset_current_path.is_file()
                and not asset_current_path.is_relative_to(self.assets_path)
            ):
                asset_target_path = self.assets_path / asset_current_path.name
                try:
                    asset_current_path.rename(asset_target_path)
                    new_path_list.append(asset_target_path)
                except OSError as e:
                    print(
                        f"Warning: Could not move asset {asset_current_path} to {asset_target_path}: {e}"
                    )
                    # Keep original path if move fails
                    new_path_list.append(asset_current_path)
            else:
                # Asset is already in the correct location or doesn't exist
                new_path_list.append(asset_current_path)

        return new_path_list

    def validate_paths(self) -> None:
        """Validate that all required paths exist.

        Raises:
            ValueError: If any required path is missing
        """
        if not self.story_folder.exists():
            raise ValueError(f"Story folder does not exist: {self.story_folder}")

        if not self.chapter_prompt_path.exists():
            raise ValueError(
                f"Chapter prompt file does not exist: {self.chapter_prompt_path}"
            )

        if not self.prompts_path.exists():
            raise ValueError(f"Prompts folder does not exist: {self.prompts_path}")

    def __str__(self) -> str:
        """String representation of VideoRecipePaths."""
        return f"VideoRecipePaths(story='{self.story_folder}', recipe='{self.recipe_name}')"

    def __repr__(self) -> str:
        """Detailed string representation of VideoRecipePaths."""
        return (
            f"VideoRecipePaths("
            f"story_folder={self.story_folder}, "
            f"chapter_prompt_path={self.chapter_prompt_path}, "
            f"recipe_name='{self.recipe_name}'"
            f")"
        )
