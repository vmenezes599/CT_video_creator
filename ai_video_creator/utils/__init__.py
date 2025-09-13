"""AI Video Creator - Utils Module"""

from .utils import (
    safe_copy,
    ensure_collection_index_exists,
    safe_move,
    get_next_available_filename,
)
from .ffmpeg_wrapper import (
    get_audio_duration,
    extend_audio_to_duration,
    create_video_segment_from_image_and_audio,
    burn_subtitles_to_video,
    concatenate_videos,
)
from .video_creator_paths import VideoCreatorPaths

__all__ = [
    "ensure_collection_index_exists",
    "safe_copy",
    "safe_move",
    "get_next_available_filename",
    "extend_audio_to_duration",
    "create_video_segment_from_image_and_audio",
    "burn_subtitles_to_video",
    "get_audio_duration",
    "concatenate_videos",
    "VideoCreatorPaths",
]
