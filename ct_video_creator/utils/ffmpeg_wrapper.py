"""FFmpeg operations for video and audio processing."""

import json
import shutil
import subprocess
from enum import Enum
from pathlib import Path

import ffmpeg
from ct_logging import logger


class SubtitlePosition(str, Enum):
    """Subtitle vertical position options."""

    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class SubtitleAlignment(str, Enum):
    """Subtitle horizontal alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


def _check_gpu_memory():
    """Check GPU memory usage to diagnose NVENC issues."""
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
                    gpu_info.append(f"GPU {i}: {used}MB/{total}MB ({usage_percent:.1f}%)")
                    logger.debug(f"GPU {i} memory: {used}MB/{total}MB ({usage_percent:.1f}%)")
            return gpu_info
        else:
            logger.debug("nvidia-smi not available or failed")
            return None
    except (FileNotFoundError, OSError):
        logger.debug("Could not check GPU memory")
        return None


def _run_ffmpeg_trace(ffmpeg_compiled: str | list[str]):
    """Run FFmpeg command with comprehensive logging."""
    try:
        result = subprocess.run(
            ffmpeg_compiled,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        )

        for line in result.stdout.splitlines():
            if line.strip():
                logger.trace(line.strip())

    except subprocess.CalledProcessError as exc:
        logger.error(f"FFmpeg exited with code {exc.returncode}")
        if exc.stdout:
            for line in exc.stdout.splitlines():
                if line.strip():
                    logger.error(f"FFmpeg: {line.strip()}")
        raise RuntimeError(f"FFmpeg failed with code {exc.returncode}") from exc


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
    duration = float(v.get("duration") or probe["format"]["duration"])
    fr = v.get("r_frame_rate", "0/1")
    if "/" in fr:
        num, den = fr.split("/")
        fps = float(num) / float(den) if float(den) != 0 else float(num)
    else:
        fps = float(fr)
    return fps, duration


def get_media_duration(path: str) -> float:
    """Get media file duration in seconds using ffmpeg.probe."""
    try:
        probe = ffmpeg.probe(path)
        duration = float(probe["format"]["duration"])
        return duration
    except Exception as e:
        raise RuntimeError(f"Failed to get audio duration for {path}: {e}") from e


def get_media_resolution(path: Path | str) -> tuple[int, int]:
    """Get media file resolution (width, height) using ffmpeg.probe."""
    try:
        probe = ffmpeg.probe(str(path))
        video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
        if not video_streams:
            raise RuntimeError(f"No video stream found in {path}")
        width = int(video_streams[0]["width"])
        height = int(video_streams[0]["height"])
        return width, height
    except Exception as e:
        raise RuntimeError(f"Failed to get media resolution for {path}: {e}") from e


def extend_audio_to_duration(
    input_path: Path,
    output_path: Path,
    extra_time_front: float = 0.0,
    extra_time_back: float = 0.0,
) -> Path:
    """Extend audio by prepending/appending *true-time* silence. Outputs AAC .m4a."""

    output_path = output_path.with_suffix(".m4a")
    if extra_time_front <= 0 and extra_time_back <= 0:
        shutil.copy2(input_path, output_path)
        return output_path

    sr = 48000  # normalize sample rate for pipeline stability

    # sanity
    if not input_path.exists():
        raise FileNotFoundError(f"Audio not found: {input_path}")

    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    fparts = []

    # 1) normalize input to 48k stereo and reset PTS
    fparts.append(f"[0:a]aresample=resampler=soxr:osr={sr},aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[ain]")

    seq = []

    # 2) optional front silence
    if extra_time_front > 0:
        fparts.append(
            f"anullsrc=channel_layout=stereo:sample_rate={sr},"
            f"atrim=0:{extra_time_front:.6f},asetpts=PTS-STARTPTS[sfront]"
        )
        seq.append("[sfront]")

    # input
    seq.append("[ain]")

    # 3) optional back silence
    if extra_time_back > 0:
        fparts.append(
            f"anullsrc=channel_layout=stereo:sample_rate={sr},"
            f"atrim=0:{extra_time_back:.6f},asetpts=PTS-STARTPTS[sback]"
        )
        seq.append("[sback]")

    # 4) concat them all (N labels → one audio)
    n = len(seq)
    fparts.append("".join(seq) + f"concat=n={n}:v=0:a=1[outa]")

    filter_complex = ";".join(fparts)

    # Choose AAC in M4A by default
    codec = "aac"
    mux_faststart = ["-movflags", "+faststart"] if output_path.suffix.lower() in {".mp4", ".m4a"} else []

    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[outa]",
        "-ar",
        f"{sr}",
        "-ac",
        "2",
        "-c:a",
        codec,
        "-b:a",
        "192k",
        *mux_faststart,
        str(output_path),
    ]

    logger.debug("Extend-audio cmd: " + " ".join(cmd))
    _run_ffmpeg_trace(cmd)
    return output_path


def extract_video_last_frame(video_path: str | Path, last_frame_output_folder: str | Path) -> Path:
    """Extract the last frame of a video as an image."""
    video_path = Path(video_path)
    last_frame_output_path = Path(last_frame_output_folder) / f"{video_path.stem}_last_frame.png"

    last_frame_output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Extracting last frame from {video_path.name} to {last_frame_output_path.name}")

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
    """Generate a video segment from an image and audio file."""
    image_path = Path(image_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    target_resolution = f"{width}:{height}"

    if not output_path.exists():
        duration = get_media_duration(str(audio_path))
        video_input = ffmpeg.input(str(image_path), loop=1, t=duration)
        audio_input = ffmpeg.input(str(audio_path))

        logger.info(f"Creating video segment: {output_path.name} (duration: {duration:.2f}s)")

        cmd = (
            ffmpeg.output(
                video_input,
                audio_input,
                str(output_path),
                r=24,
                vf=f"scale={target_resolution}",
                format="mp4",
                shortest=None,
                **{
                    "c:v": "h264_nvenc",
                    "preset": "p5",
                    "crf": "23",
                    "c:a": "aac",
                    "pix_fmt": "yuv420p",
                    "movflags": "+faststart",
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
    Final video duration matches audio duration:
    - Audio longer than video: video reverses and plays again to fill duration
    - Video longer than audio: video is cut short to match audio
    - Same duration: video plays normally with audio
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
        audio_duration = get_media_duration(str(audio_path))
        video_probe = _probe(sub_video_path)
        fps, video_duration = _fps_and_duration(video_probe)

        logger.info(f"Creating video segment from sub-video (with reverse): {output_path.name}")
        logger.debug(f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s, FPS: {fps}")

        video_input = ffmpeg.input(str(sub_video_path))
        audio_input = ffmpeg.input(str(audio_path))

        if audio_duration > video_duration:
            extra_duration = audio_duration - video_duration
            logger.debug(f"Extending video by {extra_duration:.2f}s (playing in reverse)")

            cycle_duration = video_duration * 2
            needed_cycles = int(audio_duration / cycle_duration) + 1

            cycle_frames = int(fps * cycle_duration)

            video_filter = f"scale={target_resolution}[scaled];[scaled]split=2[fwd][rev_src];[rev_src]reverse[rev];[fwd][rev]concat=n=2:v=1:a=0[cycle];[cycle]loop=loop={needed_cycles-1}:size={cycle_frames}:start=0[looped];[looped]trim=duration={audio_duration}"

        elif video_duration > audio_duration:
            logger.debug(f"Video is longer than audio, will be cut from {video_duration:.2f}s to {audio_duration:.2f}s")
            video_filter = f"scale={target_resolution}"
        else:
            video_filter = f"scale={target_resolution}"

        cmd = (
            ffmpeg.output(
                video_input,
                audio_input,
                str(output_path),
                r=fps,
                vf=video_filter,
                format="mp4",
                t=audio_duration,
                **{
                    "c:v": "h264_nvenc",
                    "preset": "p5",
                    "crf": "23",
                    "c:a": "aac",
                    "pix_fmt": "yuv420p",
                    "movflags": "+faststart",
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
    Final video duration matches audio:
    - Audio longer: freeze last frame until audio finishes
    - Video longer: cut video to match audio
    - Same duration: play normally
    """
    sub_video_path = Path(sub_video_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    target_resolution = f"{width}:{height}"

    if not sub_video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {sub_video_path}")
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

    if not output_path.exists():
        audio_duration = get_media_duration(str(audio_path))
        video_probe = _probe(sub_video_path)
        fps, video_duration = _fps_and_duration(video_probe)

        logger.info(f"Creating video segment from sub-video: {output_path.name}")
        logger.debug(f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s, FPS: {fps}")

        video_input = ffmpeg.input(str(sub_video_path))
        audio_input = ffmpeg.input(str(audio_path))

        base_1080p = (
            "scale=1920:1080:flags=lanczos:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1"
        )

        if audio_duration > video_duration:
            extra_duration = audio_duration - video_duration
            logger.debug(f"Extending video by {extra_duration:.2f}s (freezing last frame)")
            # freeze last frame AFTER we’ve normalized to 1080p
            video_filter = f"{base_1080p},tpad=stop_mode=clone:stop_duration={extra_duration}"
        else:
            if video_duration > audio_duration:
                logger.debug(
                    f"Video is longer than audio, will be cut from {video_duration:.2f}s to {audio_duration:.2f}s"
                )
            video_filter = base_1080p

        cmd = (
            ffmpeg.output(
                video_input,
                audio_input,
                str(output_path),
                r=fps,
                vf=video_filter,
                format="mp4",
                t=audio_duration,
                **{
                    "c:v": "libx264",
                    "preset": "slow",
                    "profile:v": "high",
                    "level:v": "4.2",
                    "crf": "20",  # 19=crisper / 21=smaller
                    # FIXED GOP: no scene cuts
                    "x264-params": "keyint=48:min-keyint=48:scenecut=0:bframes=3:aq-mode=2:aq-strength=1.0:psy-rd=1.0,0.0",
                    # color + audio
                    "color_primaries": "bt709",
                    "color_trc": "bt709",
                    "colorspace": "bt709",
                    "c:a": "aac",
                    "b:a": "192k",
                    "ar": "48000",
                    "ac": "2",
                    "movflags": "+faststart",
                    "pix_fmt": "yuv420p",
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
    video_path: str | Path,
    subtitle_path: str | Path,
    output_path: str | Path,
) -> Path:
    """
    Burn subtitle file into a video file.

    Args:
        video_path: Path to the input video
        subtitle_path: Path to the subtitle file (ASS or SRT format)
        output_path: Path for the output video

    Returns:
        Path to the output video file

    Note:
        For ASS files, all styling (position, margin, font size, alignment) should be
        pre-configured in the ASS file itself. Use SubtitleGenerator to create properly
        styled ASS files.
    """
    video_path = Path(video_path)
    subtitle_path = Path(subtitle_path)
    output_path = Path(output_path)

    logger.info(f"Burning subtitles to video: {video_path.name} -> {output_path.name}")
    logger.debug(f"Using subtitle file: {subtitle_path.name}")

    # For ASS files, use the ass filter (styling is baked into the file)
    # For SRT files, use the subtitles filter
    if subtitle_path.suffix.lower() == ".ass":
        subtitle_filter = f"ass={str(subtitle_path)}"
    else:
        # For SRT files, we need to specify the video resolution
        probe = _probe(video_path)
        video_stream = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
        if not video_stream:
            raise RuntimeError(f"No video stream found in {video_path}")

        width = int(video_stream["width"])
        height = int(video_stream["height"])

        subtitle_filter = f"subtitles={str(subtitle_path)}:original_size={width}x{height}"

    cmd = (
        ffmpeg.input(str(video_path))
        .output(
            str(output_path),
            vf=subtitle_filter,
            **{
                "c:v": "h264_nvenc",
                "preset": "p5",
                "crf": "23",
                "c:a": "copy",
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


def concatenate_videos_no_reencoding(video_segments: list[str | Path], output_path: str | Path) -> Path:
    """Concatenate video segments without re-encoding."""
    video_segments = [Path(segment) for segment in video_segments]
    output_path = Path(output_path)

    logger.info(f"Concatenating {len(video_segments)} video segments")

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

    if concat_list_path.exists():
        concat_list_path.unlink()

    return output_path


def concatenate_videos_with_reencoding(
    video_segments: list[str | Path],
    output_path: str | Path,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """Concatenate video segments with re-encoding to specified resolution."""
    video_segments = [Path(segment) for segment in video_segments]
    output_path = Path(output_path)

    logger.info(f"Concatenating {len(video_segments)} video segments")

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
    Preprocess each segment to 1920x1080@24 CFR with matched audio,
    apply fade-in/out (video+audio), then concat losslessly with -c copy.
    Uses libx264 CRF (better than NVENC at this res/bitrate).
    """
    video_segments = [Path(p) for p in video_segments]
    output_path = Path(output_path)
    temp_dir = output_path.parent / "temp_fade_segments"
    temp_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Concatenating {len(video_segments)} segments with {fade_duration:.2f}s fades")

    processed_segments: list[Path] = []
    concat_list_path = output_path.parent / "concat_list_fade.txt"

    try:
        for i, seg in enumerate(video_segments):
            if not seg.exists():
                raise FileNotFoundError(f"Segment not found: {seg}")
            probe = _probe(seg)
            fps, duration = _fps_and_duration(probe)
            vstream = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
            if not vstream:
                raise RuntimeError(f"No video stream in {seg}")
            has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])

            # lock fades to sane fraction of clip
            d_fade = min(fade_duration, max(0.0, duration) / 3.0)
            fade_start = max(0.0, duration - d_fade)

            # normalize to true 1080p without stretch; CFR 24; deband lightly
            base_vf = (
                f"scale={width}:{height}:flags=lanczos:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,"
                f"fps=24,gradfun=strength=0.6,"
                f"fade=t=in:st=0:d={d_fade},"
                f"fade=t=out:st={fade_start}:d={d_fade}"
            )

            # audio path: ensure stereo 48k, fade in/out
            # if clip has no audio, synth silent track to keep concat stable
            if has_audio:
                a_in = ffmpeg.input(str(seg))
                a_chain = (
                    ffmpeg.input(str(seg))
                    .audio.filter_("aresample", resampler="soxr", osr=48000)
                    .filter_("aformat", channel_layouts="stereo")
                    .filter_("volume", 1.0)
                    .filter_("afade", t="in", st=0, d=d_fade)
                    .filter_("afade", t="out", st=fade_start, d=d_fade)
                )
                a_kwargs = {"c:a": "aac", "b:a": "192k", "ar": "48000", "ac": "2"}
            else:
                # synth silence exactly clip duration
                a_chain = ffmpeg.input("anullsrc=channel_layout=stereo:sample_rate=48000", f="lavfi", t=duration)
                a_kwargs = {"c:a": "aac", "b:a": "128k", "ar": "48000", "ac": "2"}

            tmp = temp_dir / f"fade_segment_{i:03d}.mp4"
            logger.debug(f"Processing segment {i+1}/{len(video_segments)}: {seg.name} → {tmp.name}")

            # build command: one input, two streams, reencode video with x264 CRF
            (
                ffmpeg.input(str(seg))
                .output(
                    str(tmp),
                    vf=base_vf,
                    r=24,  # CFR 24
                    c_v="libx264",
                    preset="slow",
                    profile_v="high",
                    **{
                        "level:v": "4.2",
                        "crf": "20",
                        # allow smart keyframes around fades/cuts
                        "x264-params": "keyint=48:min-keyint=24:scenecut=40:bframes=3:aq-mode=2:aq-strength=1.0:psy-rd=1.0,0.0",
                        "pix_fmt": "yuv420p",
                        "color_primaries": "bt709",
                        "color_trc": "bt709",
                        "colorspace": "bt709",
                        "movflags": "+faststart",
                    },
                    **a_kwargs,
                )
                .overwrite_output()
                .global_args("-loglevel", "error")
                .run(cmd=["ffmpeg"])  # your _run_ffmpeg_trace wrapper is fine too
            )

            processed_segments.append(tmp)
            logger.debug(f"Segment {i+1} OK ({duration:.2f}s, fade {d_fade:.2f}s)")

        # concat with -c copy (streams match now)
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for p in processed_segments:
                f.write(f"file '{p.resolve()}'\n")

        logger.info("Concatenating normalized segments")
        (
            ffmpeg.input(str(concat_list_path), format="concat", safe=0)
            .output(str(output_path), c="copy", movflags="+faststart")
            .overwrite_output()
            .global_args("-loglevel", "error")
            .run(cmd=["ffmpeg"])
        )

        logger.info(f"Concat done: {output_path.name}")

    finally:
        try:
            if concat_list_path.exists():
                concat_list_path.unlink()
            for p in temp_dir.glob("*"):
                p.unlink(missing_ok=True)
            temp_dir.rmdir()
        except Exception:
            pass

    return output_path


def concatenate_videos_remove_last_frame_except_last(
    video_segments: list[str | Path],
    output_path: str | Path,
) -> Path:
    """
    Remove exactly one frame from the end of every segment except the final one,
    then concat in a single pass and encode once.
    Assumes all segments share identical stream settings (codec, fps, SAR, audio config).
    """
    video_segments = [Path(s) for s in video_segments]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # basic checks
    for i, seg in enumerate(video_segments):
        if not seg.exists():
            raise FileNotFoundError(f"Segment {i+1} not found: {seg}")
        if seg.stat().st_size < 1000:
            raise ValueError(f"Segment {i+1} too small: {seg}")

    # Probe first segment for fps (assumed identical across all)
    first_probe = _probe(video_segments[0])
    fps, _ = _fps_and_duration(first_probe)
    if fps <= 0:
        raise RuntimeError("Could not determine FPS from first segment")

    # Build ffmpeg command
    cmd = ["ffmpeg", "-y"]

    # Inputs
    for seg in video_segments:
        cmd += ["-i", str(seg)]

    # Build filter graph
    # For each input i:
    #   - get duration via lavfi metadata (we already have a helper, but we’ll rely on probe for duration)
    #   - trim end by 1/fps for all but last
    fparts = []
    v_labels = []
    a_labels = []
    for idx, seg in enumerate(video_segments):
        probe = _probe(seg)
        _, dur = _fps_and_duration(probe)
        end_trim = dur - (1.0 / fps) if idx != len(video_segments) - 1 else dur
        if end_trim < 0:
            end_trim = 0.0

        # video path: ensure pts reset; keep as-is (segments are already normalized)
        fparts.append(f"[{idx}:v]trim=start=0:end={end_trim:.6f},setpts=PTS-STARTPTS[v{idx}]")
        v_labels.append(f"[v{idx}]")

        # audio path: if present, trim to same end, resample 48k/stereo
        has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])
        if has_audio:
            fparts.append(
                f"[{idx}:a]atrim=start=0:end={end_trim:.6f},asetpts=PTS-STARTPTS,"
                f"aresample=resampler=soxr:osr=48000,aformat=channel_layouts=stereo[a{idx}]"
            )
            a_labels.append(f"[a{idx}]")
        else:
            # synth silence to keep concat stable
            fparts.append(
                f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=0:{end_trim:.6f},asetpts=PTS-STARTPTS[a{idx}]"
            )
            a_labels.append(f"[a{idx}]")

    # concat
    fparts.append("".join(v_labels + a_labels) + f"concat=n={len(video_segments)}:v=1:a=1[vout][aout]")
    filter_complex = ";".join(fparts)

    # Final encode (24 CFR, x264 CRF 20, fixed GOP 2s; no scenecut)
    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-r",
        "24",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-profile:v",
        "high",
        "-level:v",
        "4.2",
        "-crf",
        "20",
        "-x264-params",
        "keyint=48:min-keyint=48:scenecut=0:bframes=3:aq-mode=2:aq-strength=1.0:psy-rd=1.0,0.0",
        # If you prefer smarter keyframes at joins, use this instead:
        # "-x264-params", "keyint=48:min-keyint=24:scenecut=40:bframes=3:aq-mode=2:aq-strength=1.0:psy-rd=1.0,0.0",
        "-pix_fmt",
        "yuv420p",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-colorspace",
        "bt709",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    logger.debug("FFmpeg command: " + " ".join(cmd))
    try:
        _run_ffmpeg_trace(cmd)
    except RuntimeError as e:
        if output_path.exists():
            output_path.unlink()
        raise

    if not output_path.exists() or output_path.stat().st_size < 10000:
        raise RuntimeError("Final video missing or too small")

    logger.info(f"Concat (drop last frame on all but last) OK: {output_path.name}")
    return output_path


def concatenate_audio_with_silence_inbetween(
    audio_chunks: list[str | Path],
    output_path: str | Path,
    silence_duration_seconds: float = 1.0,
    fade_ms: float = 0.005,  # 5 ms micro-fades to prevent clicks
    codec: str = "aac",
    bitrate: str = "192k",
) -> Path:
    """Concatenate audio chunks with true-time silence blocks between them."""
    if not audio_chunks:
        raise ValueError("audio_chunks cannot be empty")

    audio_chunks = [Path(p) for p in audio_chunks]
    output_path = Path(output_path)
    for i, p in enumerate(audio_chunks):
        if not p.exists():
            raise FileNotFoundError(f"Audio chunk {i+1} not found: {p}")

    # Build inputs
    cmd = ["ffmpeg", "-y"]
    for p in audio_chunks:
        cmd += ["-i", str(p)]

    # Build filtergraph
    # For each input i:
    #   [i:a] -> aresample 48k, stereo -> afade in/out tiny -> [an{i}]
    # Insert N-1 silence nodes: anullsrc -> atrim=0:silence_dur -> [sil{k}]
    fparts = []
    norm_labels = []
    sr = 48000
    fade_d = max(0.0, fade_ms / 1000.0)

    for i in range(len(audio_chunks)):
        fparts.append(
            f"[{i}:a]aresample=resampler=soxr:osr={sr},"
            f"aformat=channel_layouts=stereo"
            + (f",afade=t=in:st=0:d={fade_d}" if fade_d > 0 else "")
            + (f",afade=t=out:st=END-{fade_d}:d={fade_d}" if fade_d > 0 else "")
            + f"[an{i}]"
        )
        norm_labels.append(f"[an{i}]")
        if i < len(audio_chunks) - 1:
            # precise-time silence block
            fparts.append(
                f"anullsrc=channel_layout=stereo:sample_rate={sr},"
                f"atrim=0:{silence_duration_seconds:.6f},asetpts=PTS-STARTPTS[sil{i}]"
            )

    # Interleave: a0, sil0, a1, sil1, ..., aN
    seq_labels = []
    for i in range(len(audio_chunks)):
        seq_labels.append(f"[an{i}]")
        if i < len(audio_chunks) - 1:
            seq_labels.append(f"[sil{i}]")

    fparts.append("".join(seq_labels) + f"concat=n={len(seq_labels)}:v=0:a=1[outa]")
    filter_complex = ";".join(fparts)

    # Output
    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[outa]",
        "-ar",
        f"{sr}",
        "-ac",
        "2",
        "-c:a",
        codec,
        "-b:a",
        bitrate,
        str(output_path),
    ]

    logger.debug("Audio concat cmd: " + " ".join(cmd))
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
    overlay_video: Path,
    main_video: Path,
    output_path: Path,
    start_time_seconds: int = 10,
    repeat_every_seconds: int = 60,
    position: VideoBlitPosition = VideoBlitPosition.TOP_RIGHT,
    chroma_color: str = "0x00FF00",
    similarity: float = 0.25,
    blend: float = 0.05,
    scale_percent: float = 0.30,
    max_repeats: int | None = None,
    match_fps: bool = True,
    outro_gain: float = 1.0,
    main_gain: float = 1.0,
    allow_extend_duration: bool = False,
) -> Path:
    """
    Overlay a video with green screen or alpha transparency onto a main video.

    Production-grade hardened version with:
    - Alpha compositing preferred over chromakey when available
    - Aspect ratio preservation with proper scaling
    - FPS matching to avoid stutter
    - Enhanced audio mixing with gain controls
    - SAR (Sample Aspect Ratio) handling
    - Encoder fallback (h264_nvenc → libx264)
    - Robust repeat logic without stream_loop

    Args:
        overlay_video: Path to the overlay video with green/transparent background
        main_video: Path to the main video
        output_path: Path for the output video
        start_time_seconds: Time in seconds when the overlay should first appear
        repeat_every_seconds: Repeat interval in seconds (< 0 = never repeat)
        position: Where to place the overlay (center, top-left, top-right, bottom-left, bottom-right)
        chroma_color: Hex color to key out (default: green 0x00FF00)
        similarity: Chroma key similarity threshold (0.0-1.0, default: 0.25)
        blend: Chroma key blend amount (0.0-1.0, default: 0.05)
        scale_percent: Scale factor for corner placement (default: 0.30 = 30% of main video width)
        max_repeats: Maximum number of repeats (None = unlimited within duration)
        match_fps: Match overlay FPS to main FPS to avoid stutter (default: True)
        outro_gain: Audio gain for overlay (0.0-2.0, default: 1.0)
        main_gain: Audio gain for main (0.0-2.0, default: 1.0)
        allow_extend_duration: Allow overlay to extend beyond main video duration (default: False)

    Returns:
        Path to the output video file

    Raises:
        RuntimeError: If video streams are missing or probe fails
        FileNotFoundError: If input files don't exist
    """
    # Constants for corner positioning
    CORNER_MARGIN_X = 20  # pixels from edge
    CORNER_MARGIN_Y = 20  # pixels from edge

    overlay_video = Path(overlay_video)
    main_video = Path(main_video)
    output_path = Path(output_path)

    # Validate inputs exist
    if not overlay_video.exists():
        raise FileNotFoundError(f"Overlay video not found: {overlay_video}")
    if not main_video.exists():
        raise FileNotFoundError(f"Main video not found: {main_video}")

    logger.info(f"Blitting overlay video onto main video at position: {position}")
    logger.debug(f"Overlay: {overlay_video.name}, Main: {main_video.name}")

    # Probe main video
    try:
        main_probe = _probe(main_video)
    except Exception as e:
        logger.error(f"Failed to probe main video: {e}")
        raise RuntimeError(f"Cannot probe main video: {main_video}") from e

    main_fps, main_duration = _fps_and_duration(main_probe)

    # Get main video stream with error handling
    main_video_stream = next((s for s in main_probe["streams"] if s["codec_type"] == "video"), None)
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
            f"Main SAR {main_sar}: storage {main_width}x{main_height}, " f"display {main_display_width}x{main_height}"
        )
    else:
        main_display_width = main_width

    # Check if main has audio
    main_has_audio = any(s["codec_type"] == "audio" for s in main_probe["streams"])

    logger.debug(
        f"Main video: {main_width}x{main_height} @ {main_fps:.2f}fps, "
        f"duration={main_duration:.2f}s, has_audio={main_has_audio}"
    )

    # Probe overlay video
    try:
        overlay_probe = _probe(overlay_video)
    except Exception as e:
        logger.error(f"Failed to probe overlay video: {e}")
        raise RuntimeError(f"Cannot probe overlay video: {overlay_video}") from e

    overlay_fps, overlay_duration = _fps_and_duration(overlay_probe)

    overlay_video_stream = next((s for s in overlay_probe["streams"] if s["codec_type"] == "video"), None)
    if not overlay_video_stream:
        raise RuntimeError(f"No video stream found in overlay video: {overlay_video}")

    overlay_width = int(overlay_video_stream["width"])
    overlay_height = int(overlay_video_stream["height"])
    overlay_pix_fmt = overlay_video_stream.get("pix_fmt", "")
    overlay_sar = overlay_video_stream.get("sample_aspect_ratio", "1:1")

    # Check if overlay has alpha channel
    has_alpha = "yuva" in overlay_pix_fmt or "rgba" in overlay_pix_fmt or "gbra" in overlay_pix_fmt

    # Check if overlay has audio
    overlay_has_audio = any(s["codec_type"] == "audio" for s in overlay_probe["streams"])

    logger.debug(
        f"Overlay video: {overlay_width}x{overlay_height} @ {overlay_fps:.2f}fps, "
        f"SAR={overlay_sar}, duration={overlay_duration:.2f}s, has_alpha={has_alpha}, has_audio={overlay_has_audio}"
    )

    # Step 1: Calculate overlay size - simple scale by percentage of its own size
    target_width = int(overlay_width * scale_percent)
    target_height = int(overlay_height * scale_percent)

    logger.debug(
        f"Target overlay size: {target_width}x{target_height} "
        f"({scale_percent*100:.0f}% of storage {overlay_width}x{overlay_height})"
    )

    # Step 2: Calculate position with margins
    if position == VideoBlitPosition.CENTER:
        x_pos = "(W-w)/2"
        y_pos = "(H-h)/2"
    elif position == VideoBlitPosition.TOP_LEFT:
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

    logger.debug(f"Position: {position.value} at ({x_pos}, {y_pos})")

    starts = []
    if repeat_every_seconds < 0:
        # Single overlay placement
        if start_time_seconds >= main_duration:
            logger.warning(
                f"Start time {start_time_seconds}s >= main duration {main_duration:.2f}s, overlay won't appear"
            )
        elif not allow_extend_duration and (start_time_seconds + overlay_duration) > main_duration:
            logger.warning(
                f"Start time {start_time_seconds}s would extend overlay beyond main video "
                f"({start_time_seconds + overlay_duration:.2f}s > {main_duration:.2f}s), skipping overlay. "
                f"Use allow_extend_duration=True to allow extending video duration."
            )
        else:
            starts = [start_time_seconds]
            if (start_time_seconds + overlay_duration) > main_duration:
                logger.debug(
                    f"Single overlay at t={start_time_seconds}s (duration: {overlay_duration:.2f}s) "
                    f"will extend video to {start_time_seconds + overlay_duration:.2f}s"
                )
            else:
                logger.debug(f"Single overlay at t={start_time_seconds}s (duration: {overlay_duration:.2f}s)")
    else:
        # Repeated overlay placement
        repeat_count = 0
        while True:
            t_start = start_time_seconds + (repeat_count * repeat_every_seconds)

            # When not allowing extension, stop if overlay would start at or beyond main duration
            # When allowing extension, continue generating overlays (max_repeats or reasonable limit controls this)
            if not allow_extend_duration and t_start >= main_duration:
                break  # Stop generating windows
            if max_repeats is not None and repeat_count >= max_repeats:
                break  # Capped by max_repeats

            # Safety limit: don't generate overlays that start more than 2x the main duration
            # (this prevents infinite loops when allow_extend_duration=True and max_repeats=None)
            if t_start > main_duration * 2:
                logger.warning(
                    f"Stopping overlay generation at t={t_start:.2f}s "
                    f"(exceeds 2x main duration {main_duration * 2:.2f}s)"
                )
                break

            # Check if overlay would extend beyond main video
            if not allow_extend_duration and (t_start + overlay_duration) > main_duration:
                logger.debug(
                    f"Skipping overlay at t={t_start:.2f}s (would extend to {t_start + overlay_duration:.2f}s, "
                    f"beyond main duration {main_duration:.2f}s)"
                )
            else:
                starts.append(t_start)
                if (t_start + overlay_duration) > main_duration:
                    logger.debug(f"Overlay at t={t_start:.2f}s will extend video to {t_start + overlay_duration:.2f}s")
            repeat_count += 1

        logger.debug(f"Repeated overlay: {len(starts)} appearances at times: {starts}")

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

    overlay_base_chain = []

    # Match FPS if needed to avoid stutter
    if match_fps and abs(overlay_fps - main_fps) > 0.01:
        overlay_base_chain.append(f"fps={main_fps}")
        logger.debug(f"Matching FPS: overlay {overlay_fps:.2f} → main {main_fps:.2f}")

    # Normalize SAR BEFORE scaling to ensure correct proportions
    # If SAR != 1:1, the video has non-square pixels which will cause stretching
    if overlay_sar != "1:1" and overlay_sar != "0:1":
        overlay_base_chain.append("setsar=1")
        logger.debug(f"Normalizing overlay SAR from {overlay_sar} to 1:1 before scaling")

    # Handle transparency (alpha channel or chromakey)
    if has_alpha:
        overlay_base_chain.append("format=yuva420p")
        logger.debug("Using alpha compositing (overlay has alpha channel)")
    else:
        overlay_base_chain.append(f"chromakey={chroma_color}:{similarity}:{blend},format=yuva420p")
        logger.debug(f"Using chromakey: color={chroma_color}, similarity={similarity}, blend={blend}")

    # Step 3: Scale to target dimensions
    # Use flags=bicubic for quality and eval=frame to force exact dimensions without auto-adjustment
    overlay_base_chain.append(f"scale={target_width}:{target_height}:flags=bicubic:eval=frame")
    logger.debug(f"Scaling overlay to exact {target_width}x{target_height}")

    # Trim and reset timestamps for proper overlay timing
    overlay_base_chain.append(f"trim=0:{overlay_duration},setpts=PTS-STARTPTS")
    logger.debug(f"Trimming overlay to {overlay_duration:.2f}s")

    overlay_base_str = ",".join(overlay_base_chain)

    filter_parts = []

    filter_parts.append(f"[1:v]{overlay_base_str}[overlay_base]")

    if len(starts) > 1:
        split_outputs = "".join([f"[ib{i}]" for i in range(len(starts))])
        filter_parts.append(f"[overlay_base]split={len(starts)}{split_outputs}")
    else:
        filter_parts.append("[overlay_base]null[ib0]")

    for i, start_time in enumerate(starts):
        filter_parts.append(f"[ib{i}]setpts=PTS+{start_time}/TB[iv{i}]")
        logger.debug(f"Overlay {i+1}: delaying video by {start_time:.2f}s using setpts=PTS+{start_time}/TB")

    # Calculate required output duration if extending
    if allow_extend_duration and starts:
        max_end_time = max(start + overlay_duration for start in starts)
        if max_end_time > main_duration:
            extend_duration = max_end_time - main_duration
            filter_parts.append(f"[0:v]format=yuv420p,tpad=stop_mode=clone:stop_duration={extend_duration}[base]")
            logger.debug(f"Extending base video by {extend_duration:.2f}s to accommodate overlay")
        else:
            filter_parts.append("[0:v]format=yuv420p[base]")
    else:
        filter_parts.append("[0:v]format=yuv420p[base]")

    current_label = "base"
    for i in range(len(starts)):
        next_label = f"v{i+1}" if i < len(starts) - 1 else "outv"
        # Use eof_action=pass to allow overlay to extend beyond main video when allow_extend_duration=True
        if allow_extend_duration:
            filter_parts.append(
                f"[{current_label}][iv{i}]overlay={x_pos}:{y_pos}:format=yuv420:eof_action=pass[{next_label}]"
            )
        else:
            filter_parts.append(f"[{current_label}][iv{i}]overlay={x_pos}:{y_pos}:format=yuv420[{next_label}]")
        current_label = next_label

    video_filter = ";".join(filter_parts)
    logger.debug(f"Video filter with {len(starts)} time-shifted overlays: {video_filter}")

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

    logger.debug(f"Using h264_nvenc encoder (vbr_hq, cq=28, maxrate=2200k, gop={gop_size})")

    cmd = ["ffmpeg", "-y"]

    cmd.extend(["-i", str(main_video)])
    cmd.extend(["-i", str(overlay_video)])

    if overlay_has_audio and main_has_audio:
        audio_parts = []

        audio_parts.append(f"[1:a]atrim=0:{overlay_duration},asetpts=PTS-STARTPTS,volume={outro_gain}[ia_base]")

        if len(starts) > 1:
            split_outputs = "".join([f"[iab{i}]" for i in range(len(starts))])
            audio_parts.append("[ia_base]asplit={len(starts)}{split_outputs}")
        else:
            audio_parts.append("[ia_base]anull[iab0]")

        for i, start_time in enumerate(starts):
            audio_parts.append(f"[iab{i}]asetpts=PTS+{start_time}/TB[ia{i}]")
            logger.debug(f"Overlay {i+1}: delaying audio by {start_time:.2f}s using asetpts=PTS+{start_time}/TB")

        if main_gain != 1.0:
            audio_parts.append(f"[0:a]volume={main_gain}[ma]")
            main_audio_label = "ma"
        else:
            main_audio_label = "0:a"

        audio_inputs = [f"[{main_audio_label}]"] + [f"[ia{i}]" for i in range(len(starts))]
        # Use duration=longest when allow_extend_duration=True to extend audio
        audio_duration = "longest" if allow_extend_duration else "first"
        audio_parts.append(
            f"{''.join(audio_inputs)}amix=inputs={len(starts)+1}:duration={audio_duration}:dropout_transition=2[outa]"
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
        logger.debug(f"Audio mixing: {len(starts)} overlay copies, overlay_gain={outro_gain}, main_gain={main_gain}")

    elif main_has_audio and not overlay_has_audio:
        # Only main has audio: map it with optional gain and extension
        if allow_extend_duration and starts:
            max_end_time = max(start + overlay_duration for start in starts)
            if max_end_time > main_duration:
                extend_duration = max_end_time - main_duration
                if main_gain != 1.0:
                    audio_filter = f"[0:a]volume={main_gain},apad=whole_dur={max_end_time}[outa]"
                else:
                    audio_filter = f"[0:a]apad=whole_dur={max_end_time}[outa]"
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
                logger.debug(f"Extending main audio by {extend_duration:.2f}s with silence padding")
            elif main_gain != 1.0:
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
                cmd.extend(["-filter_complex", video_filter])
                cmd.extend(["-map", "[outv]"])
                cmd.extend(["-map", "0:a"])
                output_args["c:a"] = "copy"
        elif main_gain != 1.0:
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
            cmd.extend(["-filter_complex", video_filter])
            cmd.extend(["-map", "[outv]"])
            cmd.extend(["-map", "0:a"])
            output_args["c:a"] = "copy"

        logger.debug("Using main audio only")

    elif overlay_has_audio and not main_has_audio:
        logger.warning("Overlay has audio but main doesn't - overlay audio will be ignored")
        cmd.extend(["-filter_complex", video_filter])
        cmd.extend(["-map", "[outv]"])
    else:
        cmd.extend(["-filter_complex", video_filter])
        cmd.extend(["-map", "[outv]"])
        logger.debug("No audio streams")

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

    cmd.append(str(output_path))

    try:
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        _run_ffmpeg_trace(cmd)
    except RuntimeError as e:
        logger.error(f"FFmpeg failed during overlay: {e}")
        if output_path.exists():
            output_path.unlink()
        raise

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
    Re-encode input_video to match basic settings from reference_video.
    Matches resolution, FPS, codec family, and audio settings.
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
        return next((s for s in pr.get("streams", []) if s.get("codec_type") == kind), None)

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
        return {"h264": "h264_nvenc", "hevc": "hevc_nvenc", "av1": "av1_nvenc"}.get(fam, "h264_nvenc")

    refp = _probe(reference_video)
    inp = _probe(input_video)

    rv = _first_stream(refp, "video")
    sv = _first_stream(inp, "video")
    if not rv or not sv:
        raise RuntimeError("Missing video stream in reference or input")

    ra = _first_stream(refp, "audio")
    sa = _first_stream(inp, "audio")
    has_audio = (ra is not None) and (sa is not None)

    rw, rh = int(rv["width"]), int(rv["height"])
    ref_fps = _rounded_fps(rv)
    fam = _codec_family(rv.get("codec_name") or "")
    venc = _encoder_for_family(fam)
    container = output_video.suffix.lower().lstrip(".")
    cont_args = ["-movflags", "+faststart"] if container in {"mp4", "mov"} else []

    vf_parts = [
        f"scale=w={rw}:h={rh}:force_original_aspect_ratio=decrease",
        f"pad=w={rw}:h={rh}:x=(ow-iw)/2:y=(oh-ih)/2:color=black",
        "setsar=1",
    ]
    vsync = "vfr"
    if ref_fps:
        vf_parts.append(f"fps=fps={ref_fps}")
        vsync = "cfr"

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


def add_background_music_to_video(
    video_path: Path,
    music_assets: list[Path],
    start_times: list[float],
    durations: list[float],
    volumes: list[float],
    output_path: Path,
    main_audio_volume: float = 1.0,
    fade_duration: float = 3.0,
) -> Path:
    """Add background music to video with fade in/out effects between tracks."""
    video_path = Path(video_path)
    output_path = Path(output_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not (len(music_assets) == len(start_times) == len(durations) == len(volumes)):
        raise ValueError(
            f"Parameter lists must have same length: "
            f"music_assets={len(music_assets)}, start_times={len(start_times)}, "
            f"durations={len(durations)}, volumes={len(volumes)}"
        )

    if not music_assets:
        logger.warning("No background music to add, copying video to output")
        shutil.copy2(video_path, output_path)
        return output_path

    valid_indices = []
    for i, asset in enumerate(music_assets):
        if not asset or asset == "" or asset == Path(""):
            logger.debug(f"Skipping music segment {i+1} (no asset specified)")
            continue

        asset_path = Path(asset)
        if not asset_path.exists():
            logger.warning(f"Music file not found: {asset_path}, skipping segment {i+1}")
            continue

        valid_indices.append(i)

    if not valid_indices:
        logger.info("No valid background music files, copying video to output")
        shutil.copy2(video_path, output_path)
        return output_path

    logger.info(f"Adding {len(valid_indices)} background music segments to video with fade effects")

    cmd = ["ffmpeg", "-y"]

    cmd.extend(["-i", str(video_path)])

    for idx in valid_indices:
        cmd.extend(["-i", str(music_assets[idx])])

    filter_parts = []

    for i, original_idx in enumerate(valid_indices):
        music_idx = i + 1
        duration = durations[original_idx]
        start_time = start_times[original_idx]
        volume = volumes[original_idx]
        asset = music_assets[original_idx]

        music_duration = get_media_duration(str(asset))

        # Trim/loop music to required duration
        if music_duration < duration:
            loop_count = int(duration / music_duration) + 1
            filter_parts.append(
                f"[{music_idx}:a]aloop=loop={loop_count}:size={int(music_duration * 48000)},"
                f"atrim=0:{duration},asetpts=PTS-STARTPTS[music_trimmed_{i}]"
            )
        else:
            filter_parts.append(f"[{music_idx}:a]atrim=0:{duration},asetpts=PTS-STARTPTS[music_trimmed_{i}]")

        # Apply fade in/out effects
        actual_fade_duration = min(fade_duration, duration / 2)
        is_first = i == 0
        is_last = i == len(valid_indices) - 1

        fade_filter = f"[music_trimmed_{i}]"

        if is_first and is_last:
            fade_out_start = max(0, duration - actual_fade_duration)
            fade_filter += (
                f"afade=t=in:st=0:d={actual_fade_duration},afade=t=out:st={fade_out_start}:d={actual_fade_duration}"
            )
        elif is_first:
            fade_out_start = max(0, duration - actual_fade_duration)
            fade_filter += f"afade=t=out:st={fade_out_start}:d={actual_fade_duration}"
        elif is_last:
            fade_filter += f"afade=t=in:st=0:d={actual_fade_duration}"
        else:
            fade_out_start = max(0, duration - actual_fade_duration)
            fade_filter += (
                f"afade=t=in:st=0:d={actual_fade_duration},afade=t=out:st={fade_out_start}:d={actual_fade_duration}"
            )

        fade_filter += f"[music_faded_{i}]"
        filter_parts.append(fade_filter)

        # Add delay and volume
        filter_parts.append(
            f"[music_faded_{i}]adelay={int(start_time * 1000)}|{int(start_time * 1000)}," f"volume={volume}[music_{i}]"
        )

    # Mix all music tracks
    if len(valid_indices) == 1:
        filter_parts.append("[music_0]anull[bgm_mixed]")
    else:
        music_inputs = "".join([f"[music_{i}]" for i in range(len(valid_indices))])
        filter_parts.append(
            f"{music_inputs}amix=inputs={len(valid_indices)}:duration=longest:dropout_transition=2[bgm_mixed]"
        )

    # Apply volume to video audio
    if main_audio_volume != 1.0:
        filter_parts.append(f"[0:a]volume={main_audio_volume}[main_audio]")
        main_audio_label = "main_audio"
    else:
        main_audio_label = "0:a"

    # Mix background music with video audio
    filter_parts.append(
        f"[{main_audio_label}][bgm_mixed]amix=inputs=2:duration=first:dropout_transition=2[final_audio]"
    )

    filter_complex = ";".join(filter_parts)

    cmd.extend(["-filter_complex", filter_complex])

    # Map video and audio outputs
    cmd.extend(["-map", "0:v"])
    cmd.extend(["-map", "[final_audio]"])

    # Encoding settings
    cmd.extend(
        [
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(output_path),
        ]
    )

    logger.debug(f"Adding background music with {len(valid_indices)} segments and fade effects")
    logger.debug(f"Main audio volume: {main_audio_volume}, Fade duration: {fade_duration}s")

    try:
        _run_ffmpeg_trace(cmd)
    except RuntimeError as e:
        logger.error(f"Failed to add background music: {e}")
        if output_path.exists():
            output_path.unlink()
        raise

    if not output_path.exists() or output_path.stat().st_size < 1000:
        raise RuntimeError(f"Output video is missing or too small: {output_path}")

    logger.info(f"Successfully added background music to video: {output_path.name}")
    return output_path
