"""AI Video Creator - Background Music Module"""

# Background music components
from .background_music_recipe import BackgroundMusicRecipe
from .background_music_assets import BackgroundMusicAssets, BackgroundMusicAsset
from .background_music_recipe_builder import BackgroundMusicRecipeBuilder
from .background_music_asset_manager import BackgroundMusicAssetManager


__all__ = [
    # Background music classes
    "BackgroundMusicRecipeBuilder",
    "BackgroundMusicAssetManager",
    "BackgroundMusicRecipe",
    "BackgroundMusicAssets",
    "BackgroundMusicAsset",
]
