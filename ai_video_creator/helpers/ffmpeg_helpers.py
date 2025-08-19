"""
Helpers for FFmpeg operations, including running commands and probing audio durations.
"""

import subprocess
import ffmpeg
from logging_utils import logger


def run_ffmpeg_trace(ffmpeg_compiled: str):
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
