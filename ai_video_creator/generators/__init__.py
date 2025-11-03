"""This module initializes the image generator for Flux AI."""

from .image_generator import (
    FluxAIImageGenerator,
    FluxImageRecipe,
    IImageGenerator,
    ImageRecipeBase,
)
from .video_generator import (
    IVideoGenerator,
    VideoRecipeBase,
    WanRecipeBase,
    WanI2VRecipe,
    WanT2VRecipe,
    WanGenerator,
)
from .audio_generator import (
    ZonosTTSAudioGenerator,
    ZonosTTSRecipe,
    IAudioGenerator,
    AudioRecipeBase,
)
from .background_music_generator import (
    IBackgroundMusicGenerator,
    MusicGenGenerator,
    MusicGenRecipe,
)

from .description_generator import SceneScriptGenerator, FlorenceGenerator
from .subtitle_generator import SubtitleGenerator

__all__ = [
    "IBackgroundMusicGenerator",
    "ZonosTTSAudioGenerator",
    "FluxAIImageGenerator",
    "SceneScriptGenerator",
    "SubtitleGenerator",
    "FlorenceGenerator",
    "MusicGenGenerator",
    "FluxImageRecipe",
    "IAudioGenerator",
    "IImageGenerator",
    "IVideoGenerator",
    "VideoRecipeBase",
    "ImageRecipeBase",
    "AudioRecipeBase",
    "MusicGenRecipe",
    "ZonosTTSRecipe",
    "WanRecipeBase",
    "WanI2VRecipe",
    "WanT2VRecipe",
    "WanGenerator",
]
