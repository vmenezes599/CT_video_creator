"""AI Video Creator - Utils Module"""

from .utils import (
    ensure_collection_index_exists,
    get_next_available_filename,
    safe_copy,
    safe_move,
)
from .ffmpeg_wrapper import (
    create_video_segment_from_sub_video_and_audio_freeze_last_frame,
    create_video_segment_from_sub_video_and_audio_reverse_video,
    concatenate_videos_remove_last_frame_except_last,
    create_video_segment_from_image_and_audio,
    concatenate_audio_with_silence_inbetween,
    concatenate_videos_with_fade_in_out,
    concatenate_videos_with_reencoding,
    blit_overlay_video_onto_main_video,
    concatenate_videos_no_reencoding,
    reencode_to_reference_basic,
    extract_video_last_frame,
    extend_audio_to_duration,
    burn_subtitles_to_video,
    get_audio_duration,
)
from .video_creator_paths import VideoCreatorPaths

__all__ = [
    "concatenate_videos_remove_last_frame_except_last",
    "create_video_segment_from_sub_video_and_audio_freeze_last_frame",
    "create_video_segment_from_sub_video_and_audio_reverse_video",
    "create_video_segment_from_image_and_audio",
    "concatenate_audio_with_silence_inbetween",
    "concatenate_videos_with_fade_in_out",
    "concatenate_videos_with_reencoding",
    "blit_overlay_video_onto_main_video",
    "concatenate_videos_no_reencoding",
    "ensure_collection_index_exists",
    "get_next_available_filename",
    "extend_audio_to_duration",
    "extract_video_last_frame",
    "burn_subtitles_to_video",
    "get_audio_duration",
    "VideoCreatorPaths",
    "safe_copy",
    "safe_move",
]
