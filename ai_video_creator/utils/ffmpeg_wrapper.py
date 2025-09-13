"""
Helpers for FFmpeg operations, including running commands and probing audio durations.
"""

import subprocess
from pathlib import Path

import ffmpeg
from logging_utils import logger


def _run_ffmpeg_trace(ffmpeg_compiled: str):
    """
    Run the FFmpeg command and logs its output.
    """
    # Step 2: Run with Popen to capture output
    process = subprocess.Popen(
        ffmpeg_compiled,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Step 3: Stream and log each line
    for line in process.stdout:
        logger.trace(line.strip())  # Your logger class handles output

    process.wait()

    # Optional: check exit code
    if process.returncode != 0:
        logger.error(f"FFmpeg exited with code {process.returncode}")
        raise RuntimeError(f"FFmpeg failed with code {process.returncode}")


def get_audio_duration(path: str) -> float:
    """
    Get the duration of an audio file using ffmpeg.probe
    """
    probe = ffmpeg.probe(path)
    duration = float(probe["format"]["duration"])
    return duration


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
