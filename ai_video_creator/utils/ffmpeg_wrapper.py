"""
Helpers for FFmpeg operations, including running commands and probing audio durations.
"""

from fractions import Fraction
from pathlib import Path
from enum import Enum
import subprocess
import json
import time

from logging_utils import logger
import shutil
import ffmpeg

# =============================================================================
# Helper Functions
# =============================================================================


def _check_gpu_memory():
    """
    Check GPU memory usage to help diagnose NVENC issues.
    Returns GPU memory info if available, None otherwise.
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            gpu_info = []
            for i, line in enumerate(lines):
                if line.strip():
                    used, total = map(int, line.split(", "))
                    usage_percent = (used / total) * 100
                    gpu_info.append(
                        f"GPU {i}: {used}MB/{total}MB ({usage_percent:.1f}%)"
                    )
                    logger.debug(
                        f"GPU {i} memory: {used}MB/{total}MB ({usage_percent:.1f}%)"
                    )
            return gpu_info
        else:
            logger.debug("nvidia-smi not available or failed")
            return None
    except (FileNotFoundError, OSError):
        logger.debug("Could not check GPU memory")
        return None


def _run_ffmpeg_trace(ffmpeg_compiled: str | list[str]):
    """
    Run the FFmpeg command and comprehensive logging.

    Args:
        ffmpeg_compiled: The FFmpeg command (string or list)
    """
    try:
        result = subprocess.run(
            ffmpeg_compiled,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        )

        # Log the output
        for line in result.stdout.splitlines():
            if line.strip():
                logger.trace(line.strip())

    except subprocess.CalledProcessError as exc:
        logger.error(f"FFmpeg exited with code {exc.returncode}")
        # Log stderr output if available
        if exc.stdout:
            for line in exc.stdout.splitlines():
                if line.strip():
                    logger.error(f"FFmpeg: {line.strip()}")
        raise RuntimeError(f"FFmpeg failed with code {exc.returncode}") from exc


# =============================================================================
# Core FFmpeg Functions
# =============================================================================


def _probe(path: Path) -> dict:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(r.stdout)


def _fps_and_duration(probe: dict) -> tuple[float, float]:
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    # Duration might be on stream or on format
    duration = float(v.get("duration") or probe["format"]["duration"])
    fr = v.get("r_frame_rate", "0/1")
    if "/" in fr:
        num, den = fr.split("/")
        fps = float(num) / float(den) if float(den) != 0 else float(num)
    else:
        fps = float(fr)
    return fps, duration


def _reencode_with_optional_trim(src: Path, dst: Path, trim_seconds: float | None):
    """
    Re-encode video with optional trimming.

    Args:
        src: Source video path
        dst: Destination video path
        trim_seconds: Optional number of seconds to trim to
    """
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if trim_seconds is not None:
        cmd += ["-t", f"{trim_seconds:.6f}"]
    cmd += [
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p5",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        "-pix_fmt",
        "yuv420p",
        str(dst),
    ]

    try:
        logger.debug(f"Starting re-encode: {src.name} -> {dst.name}")
        _run_ffmpeg_trace(cmd)
        logger.debug(f"Successfully processed {src.name} -> {dst.name}")
    except RuntimeError as e:
        logger.error(f"FFmpeg failed processing {src.name}: {e}")
        # Clean up partial output file
        if dst.exists():
            dst.unlink()
        raise


# =============================================================================
# Public API Functions
# =============================================================================


def get_audio_duration(path: str) -> float:
    """
    Get the duration of an audio file using ffmpeg.probe.

    Args:
        path: Path to the audio file

    Returns:
        Duration in seconds

    Raises:
        RuntimeError: If the file cannot be probed or has no duration
    """
    try:
        probe = ffmpeg.probe(path)
        duration = float(probe["format"]["duration"])
        return duration
    except Exception as e:
        raise RuntimeError(f"Failed to get audio duration for {path}: {e}") from e


def extend_audio_to_duration(
    input_path: Path,
    output_path: Path,
    extra_time_front: float = 0.0,
    extra_time_back: float = 0.0,
) -> Path:
    """
    Extend the audio clip by prepending and/or appending silence.

    Args:
        input_path: Path to the input audio file
        output_path: Path for the output audio file
        extra_time_front: Number of seconds to prepend (extend at the front)
        extra_time_back: Number of seconds to append (extend at the back)

    Returns:
        Path to the extended audio file
    """
    if extra_time_front == 0.0 and extra_time_back == 0.0:
        # No extension needed, just copy the file

        shutil.copy2(input_path, output_path)
        return output_path

    current_duration = get_audio_duration(str(input_path))

    # Build the FFmpeg filter chain
    audio_stream = ffmpeg.input(str(input_path))

    # Prepend silence if needed
    if extra_time_front > 0:
        audio_stream = audio_stream.filter(
            "adelay", f"{int(extra_time_front * 1000)}|{int(extra_time_front * 1000)}"
        )

    # Append silence if needed
    if extra_time_back > 0:
        target_duration = current_duration + extra_time_front + extra_time_back
        audio_stream = audio_stream.filter("apad")
        output_args = {
            "t": target_duration,
            "acodec": "libmp3lame",
            "format": "mp3",
        }
    else:
        target_duration = current_duration + extra_time_front
        output_args = {
            "t": target_duration,
            "acodec": "libmp3lame",
            "format": "mp3",
        }

    cmd = (
        audio_stream.output(str(output_path), **output_args)
        .overwrite_output()
        .compile()
    )

    _run_ffmpeg_trace(cmd)

    return output_path


def extract_video_last_frame(
    video_path: str | Path, last_frame_output_folder: str | Path
) -> Path:
    """
    Extract the last frame of a video as an image.

    Args:
        path: Path to the input video file
        output_path: Path for the output image file

    Returns:
        Path to the extracted image file
    """
    video_path = Path(video_path)
    last_frame_output_path = (
        Path(last_frame_output_folder) / f"{video_path.stem}_last_frame.png"
    )

    # Create output directory if it doesn't exist
    last_frame_output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        f"Extracting last frame from {video_path.name} to {last_frame_output_path.name}"
    )

    # Use select filter to get the actual last frame (frame number -1)
    # The key is to avoid raw strings and let ffmpeg-python handle the escaping
    cmd = (
        ffmpeg.input(str(video_path))
        .video.filter("reverse")
        .filter("select", "eq(n,0)")
        .output(str(last_frame_output_path), vframes=1)
        .overwrite_output()
        .compile()
    )

    _run_ffmpeg_trace(cmd)

    return last_frame_output_path


def create_video_segment_from_image_and_audio(
    image_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """
    Generate a video segment from an image and audio file.

    Args:
        image_path: Path to the image file
        audio_path: Path to the audio file
        output_path: Path where the video segment should be saved
        width: Target video width in pixels (default: 1920)
        height: Target video height in pixels (default: 1080)

    Returns:
        Path to the created video segment
    """
    image_path = Path(image_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    target_resolution = f"{width}:{height}"

    if not output_path.exists():
        duration = get_audio_duration(str(audio_path))
        video_input = ffmpeg.input(str(image_path), loop=1, t=duration)
        audio_input = ffmpeg.input(str(audio_path))

        logger.info(
            f"Creating video segment: {output_path.name} (duration: {duration:.2f}s)"
        )

        cmd = (
            ffmpeg.output(
                video_input,
                audio_input,
                str(output_path),
                r=24,  # Frame rate
                vf=f"scale={target_resolution}",  # Ensure target resolution
                format="mp4",  # Use MP4 format for concatenation
                shortest=None,
                **{
                    "c:v": "h264_nvenc",  # Re-encode video to H.264
                    "preset": "p5",  # Encoding speed/quality tradeoff
                    "crf": "23",  # Video quality (lower is better, 18–28 range)
                    "c:a": "aac",  # Audio codec
                    "pix_fmt": "yuv420p",
                    "movflags": "+faststart",  # Optimize for web streaming
                },
            )
            .overwrite_output()
            .compile()
        )
        _run_ffmpeg_trace(cmd)
        logger.info(f"Video segment created successfully: {output_path.name}")
    else:
        logger.info(f"Video segment already exists: {output_path.name}")

    return output_path


def create_video_segment_from_sub_video_and_audio_reverse_video(
    sub_video_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """
    Generate a video segment from a sub-video and audio file.
    The final video duration will always match the audio duration:
    - If audio is longer than video: the video will be reversed and played again to fill the duration
    - If video is longer than audio: the video will be cut short to match audio duration
    - If durations match: video plays normally with audio
    """
    sub_video_path = Path(sub_video_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    target_resolution = f"{width}:{height}"

    # Input validation
    if not sub_video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {sub_video_path}")
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

    if not output_path.exists():
        # Get durations of both video and audio
        audio_duration = get_audio_duration(str(audio_path))
        video_probe = _probe(sub_video_path)
        fps, video_duration = _fps_and_duration(video_probe)

        logger.info(
            f"Creating video segment from sub-video (with reverse): {output_path.name}"
        )
        logger.debug(
            f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s, FPS: {fps}"
        )

        video_input = ffmpeg.input(str(sub_video_path))
        audio_input = ffmpeg.input(str(audio_path))

        # Create video filter based on duration comparison
        if audio_duration > video_duration:
            # Audio is longer - play video forward then reverse to fill the duration
            extra_duration = audio_duration - video_duration
            logger.debug(
                f"Extending video by {extra_duration:.2f}s (playing in reverse)"
            )

            # Calculate how many full forward+reverse cycles we need
            cycle_duration = video_duration * 2  # forward + reverse
            needed_cycles = int(audio_duration / cycle_duration) + 1

            # Use video's actual frame rate instead of hardcoded 24
            cycle_frames = int(fps * cycle_duration)

            # Create forward+reverse pattern that repeats enough times to fill audio duration
            # Scale first, then split into forward and reverse, concat them, repeat the cycle, and trim
            video_filter = f"scale={target_resolution}[scaled];[scaled]split=2[fwd][rev_src];[rev_src]reverse[rev];[fwd][rev]concat=n=2:v=1:a=0[cycle];[cycle]loop=loop={needed_cycles-1}:size={cycle_frames}:start=0[looped];[looped]trim=duration={audio_duration}"

        elif video_duration > audio_duration:
            # Video is longer - cut it short to match audio duration
            logger.debug(
                f"Video is longer than audio, will be cut from {video_duration:.2f}s to {audio_duration:.2f}s"
            )
            video_filter = f"scale={target_resolution}"
        else:
            # Same duration - just scale
            video_filter = f"scale={target_resolution}"

        cmd = (
            ffmpeg.output(
                video_input,
                audio_input,
                str(output_path),
                r=fps,  # Use source video frame rate
                vf=video_filter,
                format="mp4",  # Use MP4 format for concatenation
                t=audio_duration,  # Use audio duration as the final duration
                **{
                    "c:v": "h264_nvenc",  # Re-encode video to H.264
                    "preset": "p5",  # Encoding speed/quality tradeoff
                    "crf": "23",  # Video quality (lower is better, 18–28 range)
                    "c:a": "aac",  # Audio codec
                    "pix_fmt": "yuv420p",
                    "movflags": "+faststart",  # Optimize for web streaming
                },
            )
            .overwrite_output()
            .compile()
        )
        _run_ffmpeg_trace(cmd)
        logger.info(f"Video segment created successfully: {output_path.name}")
    else:
        logger.info(f"Video segment already exists: {output_path.name}")

    return output_path


def create_video_segment_from_sub_video_and_audio_freeze_last_frame(
    sub_video_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """
    Generate a video segment from a sub-video and audio file.
    The final video duration will always match the audio duration:
    - If audio is longer than video: the last frame will be frozen until audio finishes
    - If video is longer than audio: the video will be cut short to match audio duration
    - If durations match: video plays normally with audio
    """
    sub_video_path = Path(sub_video_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    target_resolution = f"{width}:{height}"

    # Input validation
    if not sub_video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {sub_video_path}")
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

    if not output_path.exists():
        # Get durations of both video and audio
        audio_duration = get_audio_duration(str(audio_path))
        video_probe = _probe(sub_video_path)
        fps, video_duration = _fps_and_duration(video_probe)

        logger.info(f"Creating video segment from sub-video: {output_path.name}")
        logger.debug(
            f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s, FPS: {fps}"
        )

        video_input = ffmpeg.input(str(sub_video_path))
        audio_input = ffmpeg.input(str(audio_path))

        # Create video filter based on duration comparison
        if audio_duration > video_duration:
            # Audio is longer - freeze last frame
            extra_duration = audio_duration - video_duration
            logger.debug(
                f"Extending video by {extra_duration:.2f}s (freezing last frame)"
            )

            # Use tpad filter to freeze the last frame for the extra duration needed
            video_filter = f"scale={target_resolution},tpad=stop_mode=clone:stop_duration={extra_duration}"
        elif video_duration > audio_duration:
            # Video is longer - cut it short to match audio duration
            logger.debug(
                f"Video is longer than audio, will be cut from {video_duration:.2f}s to {audio_duration:.2f}s"
            )
            video_filter = f"scale={target_resolution}"
        else:
            # Same duration - just scale
            video_filter = f"scale={target_resolution}"

        cmd = (
            ffmpeg.output(
                video_input,
                audio_input,
                str(output_path),
                r=fps,  # Use source video frame rate
                vf=video_filter,
                format="mp4",  # Use MP4 format for concatenation
                t=audio_duration,  # Use audio duration as the final duration
                **{
                    "c:v": "h264_nvenc",  # Re-encode video to H.264
                    "preset": "p5",  # Encoding speed/quality tradeoff
                    "crf": "23",  # Video quality (lower is better, 18–28 range)
                    "c:a": "aac",  # Audio codec
                    "b:a": "192k",  # Audio bitrate for consistency
                    "ar": "48000",  # Audio sample rate (48kHz)
                    "ac": "2",  # Audio channels (stereo)
                    "pix_fmt": "yuv420p",
                    "movflags": "+faststart",  # Optimize for web streaming
                },
            )
            .overwrite_output()
            .compile()
        )
        _run_ffmpeg_trace(cmd)
        logger.info(f"Video segment created successfully: {output_path.name}")
    else:
        logger.info(f"Video segment already exists: {output_path.name}")

    return output_path


def burn_subtitles_to_video(
    video_path: str | Path, srt_path: str | Path, output_path: str | Path
) -> Path:
    """
    Add subtitles to a video file.

    Args:
        video_path: Path to the input video file
        srt_path: Path to the SRT subtitle file
        output_path: Path for the output video file

    Returns:
        Path to the output video with subtitles
    """
    video_path = Path(video_path)
    srt_path = Path(srt_path)
    output_path = Path(output_path)

    logger.info(f"Burning subtitles to video: {video_path.name} -> {output_path.name}")
    logger.debug(f"Using SRT file: {srt_path.name}")

    cmd = (
        ffmpeg.input(str(video_path))
        .output(
            str(output_path),
            vf=f"subtitles={str(srt_path)}",
            **{
                "c:v": "h264_nvenc",
                "preset": "p5",
                "crf": "23",
                "c:a": "aac",
                "movflags": "+faststart",
                "pix_fmt": "yuv420p",
            },
        )
        .overwrite_output()
        .compile()
    )
    _run_ffmpeg_trace(cmd)

    logger.info(f"Subtitles added successfully to: {output_path.name}")
    return output_path


def concatenate_videos_no_reencoding(
    video_segments: list[str | Path], output_path: str | Path
) -> Path:
    """
    Concatenate video segments into a single video file.

    Args:
        video_segments: List of paths to video segment files
        output_path: Path for the concatenated output video

    Returns:
        Path to the concatenated video file
    """
    video_segments = [Path(segment) for segment in video_segments]
    output_path = Path(output_path)

    logger.info(f"Concatenating {len(video_segments)} video segments")

    # Create concat list file in the same directory as output
    concat_list_path = output_path.parent / "concat_list.txt"

    with open(concat_list_path, "w", encoding="utf-8") as f:
        for segment in video_segments:
            f.write(f"file '{segment.resolve()}'\n")

    cmd = (
        ffmpeg.input(str(concat_list_path), format="concat", safe=0)
        .output(str(output_path), c="copy", **{"bsf:a": "aac_adtstoasc"})
        .overwrite_output()
        .compile()
    )
    _run_ffmpeg_trace(cmd)
    logger.info("Video concatenation completed successfully")

    # Clean up concat list file
    if concat_list_path.exists():
        concat_list_path.unlink()

    return output_path


def concatenate_videos_with_reencoding(
    video_segments: list[str | Path],
    output_path: str | Path,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """
    Concatenate video segments into a single video file with specified resolution.

    Args:
        video_segments: List of paths to video segment files
        output_path: Path for the concatenated output video
        width: Target video width in pixels (default: 1920)
        height: Target video height in pixels (default: 1080)

    Returns:
        Path to the concatenated video file
    """
    video_segments = [Path(segment) for segment in video_segments]
    output_path = Path(output_path)

    logger.info(f"Concatenating {len(video_segments)} video segments")

    # Create concat list file in the same directory as output
    concat_list_path = output_path.parent / "concat_list.txt"

    with open(concat_list_path, "w", encoding="utf-8") as f:
        for segment in video_segments:
            f.write(f"file '{segment.resolve()}'\n")

    cmd = (
        ffmpeg.input(str(concat_list_path), format="concat", safe=0)
        .output(
            str(output_path),
            vf=(
                f"zscale=w={width}:h={height}:"
                "f=spline36:"
                "primaries=bt709:transfer=bt709:matrix=bt709,"
                "format=yuv420p"
            ),
            **{
                "c:v": "h264_nvenc",
                "rc": "vbr_hq",
                "cq": "19",  # ~CRF 19-ish; tweak 18–23
                "b:v": "0",  # enable cq-based quality targeting
                "preset": "p5",  # fine
                "pix_fmt": "yuv420p",
                "movflags": "+faststart",
                "c:a": "aac",
            },
        )
        .overwrite_output()
        .compile()
    )
    _run_ffmpeg_trace(cmd)
    logger.info("Video concatenation completed successfully")

    # Clean up concat list file
    if concat_list_path.exists():
        concat_list_path.unlink()

    return output_path


def concatenate_videos_with_fade_in_out(
    video_segments: list[str | Path],
    output_path: str | Path,
    width: int = 1920,
    height: int = 1080,
    fade_duration: float = 0.4,
) -> Path:
    """
    Concatenate video segments into a single video file with fade-in and fade-out effects.

    Args:
        video_segments: List of paths to video segment files
        output_path: Path for the concatenated output video
        width: Target video width in pixels (default: 1920)
        height: Target video height in pixels (default: 1080)
        fade_duration: Duration of fade-in/fade-out effects in seconds (default: 0.4)

    Returns:
        Path to the concatenated video file

    Observations:
        If fade_duration is too long, it can appear sluggish.
    """
    video_segments = [Path(segment) for segment in video_segments]
    output_path = Path(output_path)

    logger.info(f"Concatenating {len(video_segments)} video segments with fade effects")

    # Create temporary directory for processed segments
    temp_dir = output_path.parent / "temp_fade_segments"
    temp_dir.mkdir(exist_ok=True)

    try:
        processed_segments = []

        # Process each segment with fade effects
        for i, segment in enumerate(video_segments):
            logger.debug(
                f"Processing segment {i+1}/{len(video_segments)}: {segment.name}"
            )

            # Get segment duration and FPS for processing
            probe = _probe(segment)
            fps, duration = _fps_and_duration(probe)

            # Adjust fade duration if segment is too short
            actual_fade_duration = min(fade_duration, duration / 3.0)

            temp_output = temp_dir / f"fade_segment_{i:03d}.mp4"

            # Calculate fade-out start time
            fade_start = max(0, duration - actual_fade_duration)

            # Create video filter with scaling and fade effects
            video_filter = (
                f"scale={width}:{height},"
                f"fade=t=in:st=0:d={actual_fade_duration},"
                f"fade=t=out:st={fade_start}:d={actual_fade_duration}"
            )

            # Process each segment with uniform settings
            cmd = (
                ffmpeg.input(str(segment))
                .output(
                    str(temp_output),
                    r=fps,  # Preserve original FPS of each segment
                    vf=video_filter,
                    **{
                        "c:v": "h264_nvenc",
                        "preset": "p5",
                        "crf": "23",
                        "c:a": "aac",
                        "b:a": "192k",
                        "ar": "48000",
                        "ac": "2",
                        "pix_fmt": "yuv420p",
                        "movflags": "+faststart",
                    },
                )
                .overwrite_output()
                .compile()
            )

            _run_ffmpeg_trace(cmd)
            processed_segments.append(temp_output)
            logger.debug(f"Successfully processed segment {i+1} with fade effects")

        # Create concat list file
        concat_list_path = output_path.parent / "concat_list_fade.txt"
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for segment in processed_segments:
                f.write(f"file '{segment.resolve()}'\n")

        # Concatenate processed segments
        # Copy both video and audio since segments are already processed uniformly
        logger.info("Concatenating processed segments with fade effects")
        cmd = (
            ffmpeg.input(str(concat_list_path), format="concat", safe=0)
            .output(
                str(output_path),
                **{
                    "c:v": "copy",  # Copy video (already processed)
                    "c:a": "copy",  # Copy audio (already processed and uniform)
                },
            )
            .overwrite_output()
            .compile()
        )
        _run_ffmpeg_trace(cmd)

        logger.info(
            f"Video concatenation with fade effects completed successfully: {output_path.name}"
        )

    finally:
        # Clean up temporary files
        concat_list_path = output_path.parent / "concat_list_fade.txt"
        if concat_list_path.exists():
            concat_list_path.unlink()

        if temp_dir.exists():
            for temp_file in temp_dir.glob("*"):
                temp_file.unlink(missing_ok=True)
            try:
                temp_dir.rmdir()
            except OSError:
                pass

    return output_path


def concatenate_videos_remove_last_frame_except_last(
    video_segments: list[str | Path],
    output_path: str | Path,
    max_retries: int = 3,
) -> Path:
    """
    Remove exactly one frame from the end of every segment except the final one,
    re-encode to uniform settings, then concatenate via concat demuxer (copy).

    Common reasons FFmpeg can get stuck:
    1. GPU Memory Issues: h264_nvenc can hang if GPU memory is exhausted
    2. Input File Corruption: Corrupted input files can cause infinite loops
    3. Frame Rate Issues: Unusual frame rates or variable frame rates
    4. Audio/Video Sync Problems: Mismatched audio/video streams
    5. Hardware Acceleration Failures: NVENC encoder failures
    6. Resource Contention: Multiple FFmpeg processes competing for GPU
    7. Input/Output Path Issues: Network storage or permission problems
    8. Memory Leaks: Large files causing memory exhaustion
    9. Codec Incompatibilities: Unusual codecs or formats
    10. Infinite Seeking: Seeking issues with damaged files

    Args:
        video_segments: List of video segment paths
        output_path: Output path for concatenated video
        max_retries: Maximum number of retry attempts if processing fails

    Returns:
        Path to the concatenated video file
    """
    video_segments = [Path(s) for s in video_segments]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate input segments before processing
    for i, seg in enumerate(video_segments):
        if not seg.exists():
            raise FileNotFoundError(f"Video segment {i+1} not found: {seg}")
        if seg.stat().st_size < 1000:  # Less than 1KB is suspicious
            raise ValueError(
                f"Video segment {i+1} is too small ({seg.stat().st_size} bytes): {seg}"
            )

        # Quick probe to validate the file is a valid video
        try:
            probe = _probe(seg)
            video_streams = [s for s in probe["streams"] if s["codec_type"] == "video"]
            if not video_streams:
                raise ValueError(f"No video stream found in segment {i+1}: {seg}")
        except Exception as e:
            logger.error(f"Failed to probe segment {i+1} ({seg}): {e}")
            raise ValueError(f"Invalid video segment {i+1}: {seg}") from e

    temp_dir = output_path.parent / "temp_concat_segments"

    # Check GPU memory before starting
    gpu_info = _check_gpu_memory()
    if gpu_info:
        logger.debug(f"GPU memory status: {', '.join(gpu_info)}")

    for attempt in range(max_retries):
        try:
            logger.info(f"Concatenation attempt {attempt + 1}/{max_retries}")

            # Clean up temp directory from any previous attempts
            if temp_dir.exists():
                logger.debug("Cleaning up previous temp files")
                for temp_file in temp_dir.glob("*"):
                    temp_file.unlink(missing_ok=True)
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

            temp_dir.mkdir(exist_ok=True)
            processed: list[Path] = []

            # Process each segment
            for i, seg in enumerate(video_segments):
                logger.debug(
                    f"Processing segment {i+1}/{len(video_segments)}: {seg.name}"
                )

                try:
                    probe = _probe(seg)
                    fps, duration = _fps_and_duration(probe)

                    # Log diagnostic information
                    video_stream = next(
                        s for s in probe["streams"] if s["codec_type"] == "video"
                    )
                    logger.debug(
                        f"Segment {i+1} info: codec={video_stream.get('codec_name')}, "
                        f"fps={fps:.2f}, duration={duration:.3f}s, "
                        f"resolution={video_stream.get('width')}x{video_stream.get('height')}"
                    )

                    is_last = i == len(video_segments) - 1
                    if not is_last:
                        # remove one frame: trim to duration - (1/fps)
                        target = max(0.001, duration - (1.0 / fps))
                        logger.debug(
                            f"Trimming {seg.name}: {duration:.3f}s -> {target:.3f}s (removing 1 frame at {fps:.2f} fps)"
                        )
                    else:
                        target = None  # keep intact (no trimming)
                        logger.debug(
                            f"Keeping last segment {seg.name} intact: {duration:.3f}s"
                        )

                    out = temp_dir / f"seg_{i:03d}.mp4"
                    _reencode_with_optional_trim(seg, out, target)

                    # Verify the output file was created and has reasonable size
                    if not out.exists() or out.stat().st_size < 1000:
                        raise RuntimeError(
                            f"Output segment {out.name} is missing or too small ({out.stat().st_size if out.exists() else 0} bytes)"
                        )

                    processed.append(out)
                    logger.debug(
                        f"Successfully processed segment {i+1}: {out.name} ({out.stat().st_size} bytes)"
                    )

                except (
                    subprocess.CalledProcessError,
                    RuntimeError,
                    OSError,
                ) as e:
                    logger.error(f"Failed to process segment {i+1} ({seg.name}): {e}")
                    # Add diagnostic information on failure
                    logger.error(f"Segment {i+1} path: {seg}")
                    logger.error(
                        f"Segment {i+1} size: {seg.stat().st_size if seg.exists() else 'N/A'} bytes"
                    )
                    logger.error(f"Temp output path: {temp_dir / f'seg_{i:03d}.mp4'}")
                    if (temp_dir / f"seg_{i:03d}.mp4").exists():
                        logger.error(
                            f"Partial output size: {(temp_dir / f'seg_{i:03d}.mp4').stat().st_size} bytes"
                        )
                    raise

            # Create concat list
            list_file = output_path.parent / "concat_list.txt"
            with open(list_file, "w", encoding="utf-8") as f:
                for p in processed:
                    f.write(f"file '{p.resolve()}'\n")

            logger.info(f"Concatenating {len(processed)} processed segments")

            # Final concat (stream copy—fast, no extra generation loss)
            concat_cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c",
                "copy",
                "-bsf:a",
                "aac_adtstoasc",
                str(output_path),
            ]

            try:
                logger.debug(f"Starting concatenation of {len(processed)} segments")
                _run_ffmpeg_trace(concat_cmd)
                logger.info(f"Successfully concatenated video: {output_path.name}")
            except RuntimeError as e:
                logger.error(f"Concatenation failed: {e}")
                if output_path.exists():
                    output_path.unlink()
                raise

            # Verify final output
            if not output_path.exists() or output_path.stat().st_size < 10000:
                raise RuntimeError(
                    f"Final video is missing or too small ({output_path.stat().st_size if output_path.exists() else 0} bytes)"
                )

            # Clean up on success
            list_file.unlink(missing_ok=True)
            for p in processed:
                p.unlink(missing_ok=True)
            try:
                temp_dir.rmdir()
            except OSError:
                pass

            logger.info(
                f"Video concatenation completed successfully: {output_path.name}"
            )
            return output_path.resolve()

        except (
            subprocess.CalledProcessError,
            RuntimeError,
            OSError,
        ) as e:
            logger.error(f"Concatenation attempt {attempt + 1} failed: {e}")

            # Clean up on failure
            if output_path.exists():
                output_path.unlink()
                logger.debug("Removed partial output file")

            list_file = output_path.parent / "concat_list.txt"
            if list_file.exists():
                list_file.unlink()

            # Clean up temp files
            if temp_dir.exists():
                for temp_file in temp_dir.glob("*"):
                    temp_file.unlink(missing_ok=True)
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} concatenation attempts failed")
                raise
            else:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s...
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

    # This should never be reached due to the raise in the except block
    raise RuntimeError("Concatenation failed after all retries")


def concatenate_audio_with_silence_inbetween(
    audio_chunks: list[str | Path],
    output_path: str | Path,
    silence_duration_seconds: float = 1.0,
) -> Path:
    """
    Concatenate audio chunks with silence between them.

    Args:
        audio_chunks: List of paths to audio files (must have same format/sample rate)
        output_path: Path for the output concatenated audio file
        silence_duration_seconds: Duration of silence to insert between chunks (default: 1.0)

    Returns:
        Path to the concatenated audio file

    Raises:
        ValueError: If audio_chunks is empty
        FileNotFoundError: If any input audio file doesn't exist
    """
    if not audio_chunks:
        raise ValueError("audio_chunks cannot be empty")

    audio_chunks = [Path(chunk) for chunk in audio_chunks]
    output_path = Path(output_path)

    # Validate all input files exist
    for i, chunk in enumerate(audio_chunks):
        if not chunk.exists():
            raise FileNotFoundError(f"Audio chunk {i+1} not found: {chunk}")

    # If only one chunk, just copy it
    if len(audio_chunks) == 1:
        logger.info("Only one audio chunk, copying to output")
        shutil.copy2(audio_chunks[0], output_path)
        return output_path

    logger.info(
        f"Concatenating {len(audio_chunks)} audio chunks with {silence_duration_seconds}s silence"
    )

    # Build filter_complex for concatenation with silence
    # Strategy: Use adelay to add silence after each chunk (except the last)
    filter_parts = []

    # Process each audio input: for all but last, add silence at the end
    for i in range(len(audio_chunks)):
        if i < len(audio_chunks) - 1:
            # Add padding (silence) at the end of this chunk
            filter_parts.append(f"[{i}:a]apad=pad_dur={silence_duration_seconds}[a{i}]")
        else:
            # Last chunk doesn't need padding
            filter_parts.append(f"[{i}:a]anull[a{i}]")

    # Concatenate all processed chunks
    concat_inputs = "".join([f"[a{i}]" for i in range(len(audio_chunks))])
    filter_parts.append(f"{concat_inputs}concat=n={len(audio_chunks)}:v=0:a=1[outa]")

    filter_complex = ";".join(filter_parts)

    # Build FFmpeg command
    cmd = ["ffmpeg", "-y"]

    # Add all input files
    for chunk in audio_chunks:
        cmd.extend(["-i", str(chunk)])

    # Add filter_complex
    cmd.extend(["-filter_complex", filter_complex])

    # Map output and encode
    cmd.extend(
        [
            "-map",
            "[outa]",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(output_path),
        ]
    )

    logger.debug(f"Running audio concatenation: {' '.join(cmd)}")
    _run_ffmpeg_trace(cmd)

    logger.info(f"Audio concatenation completed: {output_path.name}")
    return output_path


class VideoBlitPosition(str, Enum):
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"
    CENTER = "center"


def blit_overlay_video_onto_main_video(
    outro_video: Path,
    main_video: Path,
    output_path: Path,
    start_time_seconds: int = 10,
    repeat_every_seconds: int = 60,
    position: VideoBlitPosition = VideoBlitPosition.TOP_RIGHT,
    chroma_color: str = "0x00FF00",
    similarity: float = 0.25,
    blend: float = 0.05,
    corner_scale_percent: float = 0.30,
    max_repeats: int | None = None,
    match_fps: bool = True,
    outro_gain: float = 1.0,
    main_gain: float = 1.0,
) -> Path:
    """
    Overlay an outro video with green screen or alpha transparency onto a main video.

    Production-grade hardened version with:
    - Alpha compositing preferred over chromakey when available
    - Aspect ratio preservation with proper scaling
    - FPS matching to avoid stutter
    - Enhanced audio mixing with gain controls
    - SAR (Sample Aspect Ratio) handling
    - Encoder fallback (h264_nvenc → libx264)
    - Robust repeat logic without stream_loop

    Args:
        intro_video: Path to the intro video with green/transparent background
        main_video: Path to the main video
        output_path: Path for the output video
        start_time_seconds: Time in seconds when the intro should first appear
        repeat_every_seconds: Repeat interval in seconds (< 0 = never repeat)
        position: Where to place the intro (center, top-left, top-right, bottom-left, bottom-right)
        chroma_color: Hex color to key out (default: green 0x00FF00)
        similarity: Chroma key similarity threshold (0.0-1.0, default: 0.25)
        blend: Chroma key blend amount (0.0-1.0, default: 0.05)
        corner_scale_percent: Scale factor for corner placement (default: 0.30 = 30%)
        max_repeats: Maximum number of repeats (None = unlimited within duration)
        match_fps: Match intro FPS to main FPS to avoid stutter (default: True)
        intro_gain: Audio gain for intro (0.0-2.0, default: 1.0)
        main_gain: Audio gain for main (0.0-2.0, default: 1.0)

    Returns:
        Path to the output video file

    Raises:
        RuntimeError: If video streams are missing or probe fails
        FileNotFoundError: If input files don't exist
    """
    # Constants for corner positioning
    CORNER_MARGIN_X = 20  # pixels from edge
    CORNER_MARGIN_Y = 20  # pixels from edge

    outro_video = Path(outro_video)
    main_video = Path(main_video)
    output_path = Path(output_path)

    # Validate inputs exist
    if not outro_video.exists():
        raise FileNotFoundError(f"Intro video not found: {outro_video}")
    if not main_video.exists():
        raise FileNotFoundError(f"Main video not found: {main_video}")

    logger.info(f"Blitting intro video onto main video at position: {position}")
    logger.debug(f"Intro: {outro_video.name}, Main: {main_video.name}")

    # Probe main video
    try:
        main_probe = _probe(main_video)
    except Exception as e:
        logger.error(f"Failed to probe main video: {e}")
        raise RuntimeError(f"Cannot probe main video: {main_video}") from e

    main_fps, main_duration = _fps_and_duration(main_probe)

    # Get main video stream with error handling
    main_video_stream = next(
        (s for s in main_probe["streams"] if s["codec_type"] == "video"), None
    )
    if not main_video_stream:
        raise RuntimeError(f"No video stream found in main video: {main_video}")

    main_width = int(main_video_stream["width"])
    main_height = int(main_video_stream["height"])
    main_sar = main_video_stream.get("sample_aspect_ratio", "1:1")

    # Handle non-1:1 SAR: compute display dimensions
    if main_sar and main_sar != "1:1" and ":" in main_sar:
        sar_num, sar_den = main_sar.split(":")
        sar_ratio = float(sar_num) / float(sar_den) if float(sar_den) != 0 else 1.0
        main_display_width = int(main_width * sar_ratio)
        logger.debug(
            f"Main SAR {main_sar}: storage {main_width}x{main_height}, "
            f"display {main_display_width}x{main_height}"
        )
    else:
        main_display_width = main_width

    # Check if main has audio
    main_has_audio = any(s["codec_type"] == "audio" for s in main_probe["streams"])

    logger.debug(
        f"Main video: {main_width}x{main_height} @ {main_fps:.2f}fps, "
        f"duration={main_duration:.2f}s, has_audio={main_has_audio}"
    )

    # Probe intro video
    try:
        intro_probe = _probe(outro_video)
    except Exception as e:
        logger.error(f"Failed to probe intro video: {e}")
        raise RuntimeError(f"Cannot probe intro video: {outro_video}") from e

    intro_fps, intro_duration = _fps_and_duration(intro_probe)

    intro_video_stream = next(
        (s for s in intro_probe["streams"] if s["codec_type"] == "video"), None
    )
    if not intro_video_stream:
        raise RuntimeError(f"No video stream found in intro video: {outro_video}")

    intro_width = int(intro_video_stream["width"])
    intro_height = int(intro_video_stream["height"])
    intro_pix_fmt = intro_video_stream.get("pix_fmt", "")

    # Check if intro has alpha channel
    has_alpha = (
        "yuva" in intro_pix_fmt or "rgba" in intro_pix_fmt or "gbra" in intro_pix_fmt
    )

    # Check if intro has audio
    intro_has_audio = any(s["codec_type"] == "audio" for s in intro_probe["streams"])

    logger.debug(
        f"Intro video: {intro_width}x{intro_height} @ {intro_fps:.2f}fps, "
        f"duration={intro_duration:.2f}s, pix_fmt={intro_pix_fmt}, "
        f"has_alpha={has_alpha}, has_audio={intro_has_audio}"
    )

    # Determine scaling and positioning with aspect ratio preservation
    if position == VideoBlitPosition.CENTER:
        # Center: use native resolution but clamp to main dimensions
        target_width = min(intro_width, main_width)
        target_height = min(intro_height, main_height)

        # Preserve aspect ratio when clamping
        intro_aspect = intro_width / intro_height
        target_aspect = target_width / target_height

        if intro_aspect > target_aspect:
            # Intro is wider: constrain by width
            target_height = int(target_width / intro_aspect)
        else:
            # Intro is taller: constrain by height
            target_width = int(target_height * intro_aspect)

        x_pos = "(W-w)/2"
        y_pos = "(H-h)/2"
        logger.debug(
            f"CENTER: scaled to {target_width}x{target_height} (clamped & AR preserved)"
        )
    else:
        # Corner: scale to corner_scale_percent of smallest main dimension
        # This preserves aspect ratio and ensures intro fits
        min_main_dim = min(main_display_width, main_height)
        target_size = int(min_main_dim * corner_scale_percent)

        intro_aspect = intro_width / intro_height
        if intro_aspect > 1.0:
            # Landscape: constrain width
            target_width = target_size
            target_height = int(target_size / intro_aspect)
        else:
            # Portrait or square: constrain height
            target_height = target_size
            target_width = int(target_size * intro_aspect)

        # Calculate position based on corner
        if position == VideoBlitPosition.TOP_LEFT:
            x_pos = str(CORNER_MARGIN_X)
            y_pos = str(CORNER_MARGIN_Y)
        elif position == VideoBlitPosition.TOP_RIGHT:
            x_pos = f"W-w-{CORNER_MARGIN_X}"
            y_pos = str(CORNER_MARGIN_Y)
        elif position == VideoBlitPosition.BOTTOM_LEFT:
            x_pos = str(CORNER_MARGIN_X)
            y_pos = f"H-h-{CORNER_MARGIN_Y}"
        else:  # BOTTOM_RIGHT
            x_pos = f"W-w-{CORNER_MARGIN_X}"
            y_pos = f"H-h-{CORNER_MARGIN_Y}"

        logger.debug(
            f"Corner {position}: scaled to {target_width}x{target_height} "
            f"({corner_scale_percent*100:.0f}% of min dimension, AR preserved)"
        )

    # Build list of start times for repeated overlays
    starts = []
    if repeat_every_seconds < 0:
        # Show only once at start_time
        if start_time_seconds < main_duration:
            starts = [start_time_seconds]
            logger.debug(f"Single overlay at t={start_time_seconds}s")
        else:
            logger.warning(
                f"Start time {start_time_seconds}s >= main duration {main_duration:.2f}s, intro won't appear"
            )
    else:
        # Repeated overlays: generate start times until start >= main_duration
        repeat_count = 0
        while True:
            t_start = start_time_seconds + (repeat_count * repeat_every_seconds)
            if t_start >= main_duration:
                break  # Stop generating windows
            if max_repeats is not None and repeat_count >= max_repeats:
                break  # Capped by max_repeats
            starts.append(t_start)
            repeat_count += 1

        logger.debug(f"Repeated overlay: {len(starts)} appearances at times: {starts}")

    # If no valid start times, short-circuit: just copy main to output
    if not starts:
        logger.info("No valid overlay times, copying main video to output")
        cmd = ["ffmpeg", "-y", "-i", str(main_video), "-c", "copy", str(output_path)]
        try:
            _run_ffmpeg_trace(cmd)
        except RuntimeError as e:
            logger.error(f"FFmpeg failed during copy: {e}")
            if output_path.exists():
                output_path.unlink()
            raise

        if not output_path.exists() or output_path.stat().st_size < 1000:
            raise RuntimeError(f"Output video is missing or too small: {output_path}")
        logger.info(f"Successfully copied main video: {output_path.name}")
        return output_path

    # Build intro base processing filter chain (computed once, reused for all copies)
    intro_base_chain = []

    # Step 1: FPS matching if requested
    if match_fps and abs(intro_fps - main_fps) > 0.01:
        intro_base_chain.append(f"fps={main_fps}")
        logger.debug(f"Matching FPS: intro {intro_fps:.2f} → main {main_fps:.2f}")

    # Step 2: Alpha compositing vs chromakey
    if has_alpha:
        # Prefer alpha compositing: ensure proper alpha format
        intro_base_chain.append("format=yuva420p")
        logger.debug("Using alpha compositing (intro has alpha channel)")
    else:
        # Use chromakey to remove chroma_color and convert to yuva
        intro_base_chain.append(
            f"chromakey={chroma_color}:{similarity}:{blend},format=yuva420p"
        )
        logger.debug(
            f"Using chromakey: color={chroma_color}, similarity={similarity}, blend={blend}"
        )

    # Step 3: Scale with aspect ratio preserved
    intro_base_chain.append(
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease"
    )

    # Step 4: Trim to intro duration and reset PTS to start from 0
    intro_base_chain.append(f"trim=0:{intro_duration},setpts=PTS-STARTPTS")
    logger.debug(f"Trimming intro to {intro_duration:.2f}s and resetting PTS")

    # Combine intro base filter chain
    intro_base_str = ",".join(intro_base_chain)

    # Build filter_complex with time-shifted copies
    filter_parts = []

    # Create the base intro stream (computed once)
    filter_parts.append(f"[1:v]{intro_base_str}[intro_base]")

    # Split intro_base into N outputs (one for each appearance)
    if len(starts) > 1:
        split_outputs = "".join([f"[ib{i}]" for i in range(len(starts))])
        filter_parts.append(f"[intro_base]split={len(starts)}{split_outputs}")
    else:
        # No split needed for single appearance
        filter_parts.append("[intro_base]null[ib0]")

    # Create time-shifted copies for each start time
    for i, start_time in enumerate(starts):
        filter_parts.append(f"[ib{i}]setpts=PTS+{start_time}/TB[iv{i}]")

    # Normalize main video to yuv420p
    filter_parts.append("[0:v]format=yuv420p[base]")

    # Chain overlays sequentially
    current_label = "base"
    for i in range(len(starts)):
        next_label = f"v{i+1}" if i < len(starts) - 1 else "outv"
        filter_parts.append(
            f"[{current_label}][iv{i}]overlay={x_pos}:{y_pos}:format=yuv420[{next_label}]"
        )
        current_label = next_label

    video_filter = ";".join(filter_parts)
    logger.debug(
        f"Video filter with {len(starts)} time-shifted overlays: {video_filter}"
    )

    # Build output arguments
    # Calculate GOP size (2 seconds worth of frames)
    gop_size = int(main_fps * 2)

    output_args = {
        "pix_fmt": "yuv420p",
        "movflags": "+faststart",
        "c:v": "h264_nvenc",
        "preset": "p5",
        "rc": "vbr_hq",
        "cq": "28",
        "b:v": "0",
        "maxrate": "2200k",
        "bufsize": "4400k",
        "g": str(gop_size),
        "bf": "3",
    }

    logger.debug(
        f"Using h264_nvenc encoder (vbr_hq, cq=28, maxrate=2200k, gop={gop_size})"
    )

    # Build FFmpeg command manually to handle multiple -map arguments
    # (ffmpeg-python doesn't support duplicate keyword args)

    cmd = ["ffmpeg", "-y"]

    # Input files
    cmd.extend(["-i", str(main_video)])
    cmd.extend(["-i", str(outro_video)])

    # Filter complex with audio handling
    if intro_has_audio and main_has_audio:
        # Both have audio: create time-shifted audio copies and mix
        audio_parts = []

        # Create intro audio base: trim and reset PTS
        audio_parts.append(
            f"[1:a]atrim=0:{intro_duration},asetpts=PTS-STARTPTS,volume={outro_gain}[ia_base]"
        )

        # Split audio base into N outputs
        if len(starts) > 1:
            split_outputs = "".join([f"[iab{i}]" for i in range(len(starts))])
            audio_parts.append("[ia_base]asplit={len(starts)}{split_outputs}")
        else:
            audio_parts.append("[ia_base]anull[iab0]")

        # Create time-shifted audio copies for each start time
        for i, start_time in enumerate(starts):
            audio_parts.append(f"[iab{i}]asetpts=PTS+{start_time}/TB[ia{i}]")

        # Apply main audio volume if needed
        if main_gain != 1.0:
            audio_parts.append(f"[0:a]volume={main_gain}[ma]")
            main_audio_label = "ma"
        else:
            main_audio_label = "0:a"

        # Mix all audio streams
        audio_inputs = [f"[{main_audio_label}]"] + [
            f"[ia{i}]" for i in range(len(starts))
        ]
        audio_parts.append(
            f"{''.join(audio_inputs)}amix=inputs={len(starts)+1}:duration=first:dropout_transition=2[outa]"
        )

        audio_filter = ";".join(audio_parts)
        full_filter_complex = f"{video_filter};{audio_filter}"
        cmd.extend(["-filter_complex", full_filter_complex])
        cmd.extend(["-map", "[outv]"])
        cmd.extend(["-map", "[outa]"])

        output_args.update(
            {
                "c:a": "aac",
                "b:a": "192k",
                "ar": "48000",
            }
        )
        logger.debug(
            f"Audio mixing: {len(starts)} intro copies, intro_gain={outro_gain}, main_gain={main_gain}"
        )

    elif main_has_audio and not intro_has_audio:
        # Only main has audio: map it with optional gain
        if main_gain != 1.0:
            audio_filter = f"[0:a]volume={main_gain}[outa]"
            full_filter_complex = f"{video_filter};{audio_filter}"
            cmd.extend(["-filter_complex", full_filter_complex])
            cmd.extend(["-map", "[outv]"])
            cmd.extend(["-map", "[outa]"])

            output_args.update(
                {
                    "c:a": "aac",
                    "b:a": "192k",
                    "ar": "48000",
                }
            )
        else:
            # No gain adjustment: copy audio
            cmd.extend(["-filter_complex", video_filter])
            cmd.extend(["-map", "[outv]"])
            cmd.extend(["-map", "0:a"])
            output_args["c:a"] = "copy"

        logger.debug("Using main audio only")

    elif intro_has_audio and not main_has_audio:
        # Only intro has audio: not typical but handle it
        logger.warning("Intro has audio but main doesn't - intro audio will be ignored")
        cmd.extend(["-filter_complex", video_filter])
        cmd.extend(["-map", "[outv]"])
    else:
        # Neither has audio
        cmd.extend(["-filter_complex", video_filter])
        cmd.extend(["-map", "[outv]"])
        logger.debug("No audio streams")

    # Add output arguments
    for key, value in output_args.items():
        if key == "c:v" or key == "c:a":
            cmd.extend([f"-{key}", value])
        elif key == "b:a" or key == "b:v":
            cmd.extend([f"-{key}", value])
        elif key == "ar":
            cmd.extend(["-ar", value])
        elif key == "preset":
            cmd.extend(["-preset", value])
        elif key == "crf":
            cmd.extend(["-crf", value])
        elif key == "cq":
            cmd.extend(["-cq", value])
        elif key == "rc":
            cmd.extend(["-rc", value])
        elif key == "maxrate":
            cmd.extend(["-maxrate", value])
        elif key == "bufsize":
            cmd.extend(["-bufsize", value])
        elif key == "g":
            cmd.extend(["-g", value])
        elif key == "bf":
            cmd.extend(["-bf", value])
        elif key == "pix_fmt":
            cmd.extend(["-pix_fmt", value])
        elif key == "movflags":
            cmd.extend(["-movflags", value])

    # Output file
    cmd.append(str(output_path))

    # Run with enhanced error handling
    try:
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        _run_ffmpeg_trace(cmd)
    except RuntimeError as e:
        logger.error(f"FFmpeg failed during overlay: {e}")
        # Clean up partial output
        if output_path.exists():
            output_path.unlink()
        raise

    # Verify output was created
    if not output_path.exists() or output_path.stat().st_size < 1000:
        raise RuntimeError(
            f"Output video is missing or too small: {output_path} "
            f"({output_path.stat().st_size if output_path.exists() else 0} bytes)"
        )

    logger.info(f"Successfully created video with intro overlay: {output_path.name}")
    return output_path


def reencode_to_reference_basic(
    input_video: Path,
    reference_video: Path,
    output_video: Path,
) -> Path:
    """
    Always re-encode input_video to match basic settings from reference_video:
      - Resolution: match reference (preserve AR via scale+pad, setsar=1)
      - FPS: match rounded integer FPS of reference (e.g., 29.97 -> 30) if known
      - Codec family: NVENC flavor chosen by reference (h264/hevc/av1), fallback h264
      - Pixel format: yuv420p for broad compatibility
      - Audio: if ref has audio and input has audio -> AAC 160k stereo @ 48k; else -an

    Requires: _probe(path) -> ffprobe dict, _run_ffmpeg_trace(cmd: list) -> None
    """
    input_video = Path(input_video)
    reference_video = Path(reference_video)
    output_video = Path(output_video)

    if not input_video.exists():
        raise FileNotFoundError(input_video)
    if not reference_video.exists():
        raise FileNotFoundError(reference_video)
    if input_video.resolve() == output_video.resolve():
        raise ValueError("output_video must differ from input_video")
    output_video.parent.mkdir(parents=True, exist_ok=True)

    # --- local helpers (kept inside to satisfy “one function”) ---
    def _first_stream(pr, kind):
        return next(
            (s for s in pr.get("streams", []) if s.get("codec_type") == kind), None
        )

    def _rounded_fps(stream):
        r = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/0"
        try:
            num, den = map(int, r.split("/"))
            if num == 0 or den == 0:
                return None
            return int(round(num / den))
        except Exception:
            return None

    def _codec_family(name: str) -> str:
        n = (name or "").lower()
        if "264" in n or n in {"h264", "avc"}:
            return "h264"
        if "265" in n or n in {"hevc", "h265"}:
            return "hevc"
        if "av1" in n:
            return "av1"
        return "h264"

    def _encoder_for_family(fam: str) -> str:
        return {"h264": "h264_nvenc", "hevc": "hevc_nvenc", "av1": "av1_nvenc"}.get(
            fam, "h264_nvenc"
        )

    # --- probe ---
    refp = _probe(reference_video)
    inp = _probe(input_video)

    rv = _first_stream(refp, "video")
    sv = _first_stream(inp, "video")
    if not rv or not sv:
        raise RuntimeError("Missing video stream in reference or input")

    ra = _first_stream(refp, "audio")
    sa = _first_stream(inp, "audio")
    has_audio = (ra is not None) and (sa is not None)

    # --- reference targets ---
    rw, rh = int(rv["width"]), int(rv["height"])
    ref_fps = _rounded_fps(rv)  # int or None
    fam = _codec_family(rv.get("codec_name") or "")
    venc = _encoder_for_family(fam)
    container = output_video.suffix.lower().lstrip(".")
    cont_args = ["-movflags", "+faststart"] if container in {"mp4", "mov"} else []

    # --- filters: always scale+pad to exact ref; set fps if known ---
    vf_parts = [
        f"scale=w={rw}:h={rh}:force_original_aspect_ratio=decrease",
        f"pad=w={rw}:h={rh}:x=(ow-iw)/2:y=(oh-ih)/2:color=black",
        "setsar=1",
    ]
    vsync = "vfr"
    if ref_fps:
        vf_parts.append(f"fps=fps={ref_fps}")
        vsync = "cfr"

    # --- video encode: simple & deterministic ---
    v_args = [
        "-c:v",
        venc,
        "-preset",
        "p5",
        "-rc",
        "vbr",
        "-cq",
        "23",
        "-pix_fmt",
        "yuv420p",
    ]

    # --- audio: mirror presence, keep it simple ---
    if has_audio:
        a_args = [
            "-map",
            "0:a:0",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-ac",
            "2",
        ]
    else:
        a_args = ["-an"]

    # --- build & run ---
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_video),
        "-map",
        "0:v:0",
        "-vf",
        ",".join(vf_parts),
        *v_args,
        *a_args,
        "-sn",
        "-dn",
        *cont_args,
        "-vsync",
        vsync,
        str(output_video),
    ]

    logger.debug("FFmpeg cmd: %s", " ".join(map(str, cmd)))
    _run_ffmpeg_trace(cmd)

    if not output_video.exists() or output_video.stat().st_size < 1024:
        raise RuntimeError(f"Output missing/too small: {output_video}")
    return output_video
