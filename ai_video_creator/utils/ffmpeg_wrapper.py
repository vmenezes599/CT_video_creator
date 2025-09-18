"""
Helpers for FFmpeg operations, including running commands and probing audio durations.
"""

import json
import subprocess
import time
from pathlib import Path

import ffmpeg
from logging_utils import logger


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
            timeout=10,
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
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        logger.debug("Could not check GPU memory")
        return None


def _run_ffmpeg_trace(ffmpeg_compiled: str | list[str], timeout: int | None = None):
    """
    Run the FFmpeg command with timeout and comprehensive logging.

    Args:
        ffmpeg_compiled: The FFmpeg command (string or list)
        timeout: Optional timeout in seconds
    """
    try:
        result = subprocess.run(
            ffmpeg_compiled,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
            timeout=timeout,
        )

        # Log the output
        for line in result.stdout.splitlines():
            if line.strip():
                logger.trace(line.strip())

    except subprocess.TimeoutExpired as exc:
        logger.error(f"FFmpeg process timed out after {timeout} seconds")
        raise RuntimeError(f"FFmpeg process timed out after {timeout} seconds") from exc
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


def _reencode_with_optional_trim(
    src: Path, dst: Path, trim_seconds: float | None, timeout: int = 300
):
    """
    Re-encode video with optional trimming and timeout.

    Args:
        src: Source video path
        dst: Destination video path
        trim_seconds: Optional number of seconds to trim to
        timeout: Timeout in seconds for the operation
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
        _run_ffmpeg_trace(cmd, timeout=timeout)
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
    input_path: Path, output_path: Path, extra_time: float
) -> Path:
    """
    Extend the audio clip to the target duration.

    Args:
        input_path: Path to the input audio file
        output_path: Path for the output audio file
        extra_time: Number of seconds to extend the audio

    Returns:
        Path to the extended audio file
    """
    current_duration = get_audio_duration(str(input_path))
    target_duration = current_duration + extra_time

    cmd = (
        ffmpeg.input(str(input_path))
        .filter("apad")
        .output(
            str(output_path),
            t=target_duration,
            acodec="libmp3lame",
            format="mp3",
        )
        .overwrite_output()
        .compile()
    )

    _run_ffmpeg_trace(cmd)

    return output_path


def create_video_segment_from_image_and_audio(
    image_path: str | Path, audio_path: str | Path, output_path: str | Path
) -> Path:
    """
    Generate a video segment from an image and audio file.

    Args:
        image_path: Path to the image file
        audio_path: Path to the audio file
        output_path: Path where the video segment should be saved

    Returns:
        Path to the created video segment
    """
    image_path = Path(image_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)

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
                vf="scale=1280:720",  # Ensure 720p resolution
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


def create_video_segment_from_sub_video_and_audio(
    sub_video_path: str | Path, audio_path: str | Path, output_path: str | Path
):
    """
    Generate a video segment from a sub-video and audio file.
    """
    sub_video_path = Path(sub_video_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)

    if not output_path.exists():
        video_input = ffmpeg.input(str(sub_video_path))
        audio_input = ffmpeg.input(str(audio_path))

        logger.info(f"Creating video segment from sub-video: {output_path.name}")

        cmd = (
            ffmpeg.output(
                video_input,
                audio_input,
                str(output_path),
                r=24,  # Frame rate
                vf="scale=1280:720",  # Ensure 720p resolution
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


def concatenate_videos(
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

    if not output_path.exists():
        cmd = (
            ffmpeg.input(str(concat_list_path), format="concat", safe=0)
            .output(str(output_path), c="copy", **{"bsf:a": "aac_adtstoasc"})
            .overwrite_output()
            .compile()
        )
        _run_ffmpeg_trace(cmd)
        logger.info("Video concatenation completed successfully")
    else:
        logger.info(f"Final video already exists: {output_path.name}")

    # Clean up concat list file
    if concat_list_path.exists():
        concat_list_path.unlink()

    return output_path


def concatenate_videos_remove_last_frame_except_last(
    video_segments, output_path, max_retries: int = 3, timeout: int = 300
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
        timeout: Timeout in seconds for individual FFmpeg operations

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

    # If output already exists, return it
    if output_path.exists():
        index = 1
        new_output_path = output_path.with_stem(output_path.stem + f"_{index}")
        while new_output_path.exists():
            index += 1
            new_output_path = output_path.with_stem(output_path.stem + f"_{index}")
        output_path = new_output_path
        logger.debug(f"Output file exists, using new path: {output_path}")

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
                    _reencode_with_optional_trim(seg, out, target, timeout)

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
                    subprocess.TimeoutExpired,
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
                _run_ffmpeg_trace(concat_cmd, timeout=timeout * 2)
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
            return output_path

        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
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
