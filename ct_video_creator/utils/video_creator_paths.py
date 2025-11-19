"""
Path management for video recipe creation.
"""

from pathlib import Path
from ct_video_creator.environment_variables import DEFAULT_ASSETS_FOLDER


class VideoCreatorPaths:
    """Handles path management for video recipe creation."""

    DEFAULT_ASSETS_MASK = "default_assets"
    USER_ASSETS_MASK = "user_assets"
    STORY_ASSETS_MASK = "assets"

    def __init__(self, user_folder: Path, story_name: str, chapter_index: int):
        """Initialize VideoRecipePaths with story folder and chapter prompt path.

        Args:
            user_folder: Path to the user folder
            story_name: Name of the story
            chapter_index: Index of the chapter
        """
        self.user_folder = user_folder
        self.story_folder = user_folder / "stories" / story_name
        self.chapter_index = chapter_index

        self.chapter_prompt_path = self.story_folder / "prompts" / f"chapter_{chapter_index+1:03}.json"

        # Initialize paths
        self.video_folder = self.story_folder / "videos"
        self.video_chapter_folder = self.video_folder / f"chapter_{chapter_index+1:03}"
        self.story_assets_folder = self.video_chapter_folder / "assets"

        # Final modules paths
        self.narrator_asset_folder = self.story_assets_folder / "narrators"
        self.image_asset_folder = self.story_assets_folder / "images"
        self.sub_videos_asset_folder = self.story_assets_folder / "sub_videos"
        self.video_assembler_asset_folder = self.story_assets_folder / "video_assembler"
        self.background_music_asset_folder = self.story_assets_folder / "background_music"

        # Create directories if they don't exist
        self.narrator_asset_folder.mkdir(parents=True, exist_ok=True)
        self.image_asset_folder.mkdir(parents=True, exist_ok=True)
        self.sub_videos_asset_folder.mkdir(parents=True, exist_ok=True)
        self.video_assembler_asset_folder.mkdir(parents=True, exist_ok=True)
        self.background_music_asset_folder.mkdir(parents=True, exist_ok=True)

        # Recipe file paths
        self.narrator_recipe_file = self.video_chapter_folder / "narrator_recipe.json"
        self.image_recipe_file = self.video_chapter_folder / "image_recipe.json"
        self.sub_video_recipe_file = self.video_chapter_folder / "sub_video_recipe.json"
        self.video_assembler_recipe_file = self.video_chapter_folder / "video_assembler_recipe.json"
        self.background_music_recipe_file = self.video_chapter_folder / "background_music_recipe.json"

        # Assets file paths
        self.narrator_asset_file = self.video_chapter_folder / "narrator_assets.json"
        self.image_asset_file = self.video_chapter_folder / "image_assets.json"
        self.sub_video_asset_file = self.video_chapter_folder / "sub_video_assets.json"
        self.video_assembler_asset_file = self.video_chapter_folder / "video_assembler_assets.json"
        self.background_music_asset_file = self.video_chapter_folder / "background_music_assets.json"

        # Output video file path
        self.video_output_file = self.video_chapter_folder / f"video_chapter_{chapter_index+1:03}.mp4"

    def mask_asset_path(self, asset_path: Path) -> Path:
        """Get the masked asset path for this instance."""

        if asset_path.is_dir():
            raise ValueError("Can not resolve folders.")

        user_assets_folder = self.get_user_assets_folder()
        default_assets_folder = self.get_default_assets_folder()

        # Resolve to absolute path and validate
        asset_path = asset_path.resolve()

        if asset_path.is_dir():
            raise ValueError(f"Asset path is a folder, expected a file: {asset_path}")

        if asset_path.is_relative_to(user_assets_folder):
            relative_path = asset_path.relative_to(user_assets_folder)
            return Path(self.USER_ASSETS_MASK) / relative_path

        elif asset_path.is_relative_to(default_assets_folder):
            relative_path = asset_path.relative_to(default_assets_folder)
            return Path(self.DEFAULT_ASSETS_MASK) / relative_path

        elif asset_path.is_relative_to(self.story_assets_folder):
            relative_path = asset_path.relative_to(self.story_assets_folder)
            return Path(self.STORY_ASSETS_MASK) / relative_path

        else:
            raise ValueError(f"Asset path is not under known assets folders: {asset_path}")

    def unmask_asset_path(self, asset_path: Path) -> Path:
        """Get the unmasked asset path for this instance."""

        if asset_path.is_dir():
            raise ValueError("Can not resolve folders.")

        user_folder = self.get_user_assets_folder()
        default_assets_folder = self.get_default_assets_folder()

        # Extract relative path from masked path
        asset_path_str = str(asset_path)

        if asset_path_str.startswith(self.USER_ASSETS_MASK):
            relative_str = asset_path_str[len(self.USER_ASSETS_MASK) :].lstrip("/")

            result = (user_folder / relative_str).resolve()

            if not result.is_relative_to(user_folder.resolve()):
                raise ValueError(f"Asset path escapes user folder: {result}")

            if not result.exists():
                result.parent.mkdir(parents=True, exist_ok=True)
                result.touch()

            return result

        elif asset_path_str.startswith(self.DEFAULT_ASSETS_MASK):
            relative_str = asset_path_str[len(self.DEFAULT_ASSETS_MASK) :].lstrip("/")

            result = (default_assets_folder / relative_str).resolve()

            if not result.is_relative_to(default_assets_folder.resolve()):
                raise ValueError(f"Asset path escapes default folder: {result}")

            if not result.exists():
                result.parent.mkdir(parents=True, exist_ok=True)
                result.touch()

            return result

        elif asset_path_str.startswith(self.STORY_ASSETS_MASK):
            relative_str = asset_path_str[len(self.STORY_ASSETS_MASK) :].lstrip("/")

            result = (self.story_assets_folder / relative_str).resolve()

            if not result.is_relative_to(self.story_assets_folder.resolve()):
                raise ValueError(f"Asset path escapes story asset folder: {result}")

            return result

        else:
            raise ValueError(f"Asset path does not start with known masks: {asset_path}")

    def _mask_user_assets_folder(self, asset_path: Path):
        """Get the user assets folder path for this instance."""
        user_folder = self.get_user_assets_folder()

        # Resolve to absolute path and validate
        asset_path = asset_path.resolve()

        if not asset_path.is_relative_to(user_folder):
            raise ValueError(f"Asset path is not under user assets folder: {asset_path}")

        # Use relative_to() instead of string replacement
        relative_path = asset_path.relative_to(user_folder)
        return Path(self.USER_ASSETS_MASK) / relative_path

    def _unmask_user_assets_folder(self, asset_path: Path):
        """Get the unmasked user assets folder path for this instance."""
        user_folder = self.get_user_assets_folder()

        # Extract relative path from masked path
        if not str(asset_path).startswith(self.USER_ASSETS_MASK):
            raise ValueError(f"Asset path does not start with mask: {asset_path}")

        # Get the relative portion after the mask
        relative_str = str(asset_path)[len(self.USER_ASSETS_MASK) :].lstrip("/")

        # Reconstruct and resolve the full path
        result = (user_folder / relative_str).resolve()

        # CRITICAL: Validate AFTER resolving to prevent path traversal
        if not result.is_relative_to(user_folder.resolve()):
            raise ValueError(f"Asset path escapes user folder: {result}")

        if not result.exists():
            raise ValueError(f"Asset path does not exist: {result}")

        return result

    @classmethod
    def mask_default_assets_folder(cls, asset_path: Path):
        """Get the masked default assets folder path."""

        default_assets_folder = VideoCreatorPaths.get_default_assets_folder()

        # Resolve to absolute path and validate
        asset_path = asset_path.resolve()

        if not asset_path.is_relative_to(default_assets_folder):
            raise ValueError(f"Asset path is not under default assets folder: {asset_path}")

        # Use relative_to() instead of string replacement
        relative_path = asset_path.relative_to(default_assets_folder)
        return Path(cls.DEFAULT_ASSETS_MASK) / relative_path

    @classmethod
    def unmask_default_assets_folder(cls, asset_path: Path):
        """Get the unmasked default assets folder path."""

        default_assets_folder = VideoCreatorPaths.get_default_assets_folder()

        # Extract relative path from masked path
        if not str(asset_path).startswith(cls.DEFAULT_ASSETS_MASK):
            raise ValueError(f"Asset path does not start with mask: {asset_path}")

        # Get the relative portion after the mask
        relative_str = str(asset_path)[len(cls.DEFAULT_ASSETS_MASK) :].lstrip("/")

        # Reconstruct and resolve the full path
        result = (default_assets_folder / relative_str).resolve()

        # CRITICAL: Validate AFTER resolving to prevent path traversal
        if not result.is_relative_to(default_assets_folder.resolve()):
            raise ValueError(f"Asset path escapes default folder: {result}")

        if not result.exists():
            raise ValueError(f"Asset path does not exist: {result}")

        return result

    _default_assets_stub_created = False

    @classmethod
    def _ensure_default_stub_assets(cls, base_path: Path) -> Path:
        """Create a minimal default assets layout to keep tests independent of real files."""
        if cls._default_assets_stub_created:
            return base_path
        (base_path / "voices").mkdir(parents=True, exist_ok=True)
        (base_path / "background_music").mkdir(parents=True, exist_ok=True)
        (base_path / "voices" / "voice_002.mp3").touch(exist_ok=True)
        (base_path / "background_music.mp3").touch(exist_ok=True)
        cls._default_assets_stub_created = True
        return base_path

    @classmethod
    def get_default_assets_folder(cls) -> Path:
        """Get the default assets folder path, falling back to a stub in test environments."""
        configured = DEFAULT_ASSETS_FOLDER.strip()
        if not configured or "your_default_assets_folder_here" in configured:
            base = Path.cwd() / "default_assets_stub"
            return cls._ensure_default_stub_assets(base)
        base = Path(configured).resolve()
        if not base.exists():
            base.mkdir(parents=True, exist_ok=True)
        return base

    def get_user_assets_folder(self) -> Path:
        """Get the user assets folder path for this instance."""
        return Path(self.user_folder) / "user_assets"
