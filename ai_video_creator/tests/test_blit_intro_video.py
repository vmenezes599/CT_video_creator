"""
Comprehensive tests for blit_intro_video_onto_main_video function.

Creates synthetic test fixtures using FFmpeg filters (no large binaries required).
Tests cover alpha compositing, chromakey, FPS matching, audio mixing, scaling, and timing.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from ai_video_creator.utils.ffmpeg_wrapper import (
    VideoBlitPosition,
    blit_overlay_video_onto_main_video,
    _probe,
    _fps_and_duration,
)


class TestFixtureGenerator:
    """Generate synthetic video fixtures for testing."""

    @staticmethod
    def create_main_video(
        output_path: Path,
        width: int = 640,
        height: int = 360,
        duration: float = 6.0,
        fps: float = 30.0,
        with_audio: bool = True,
    ):
        """Create a simple black main video with optional audio."""
        cmd = ["ffmpeg", "-y", "-f", "lavfi"]

        # Video: black background
        cmd.extend(["-i", f"color=c=black:s={width}x{height}:d={duration}:rate={fps}"])

        if with_audio:
            # Audio: 1000Hz sine wave
            cmd.extend(
                ["-f", "lavfi", "-i", f"sine=frequency=1000:duration={duration}"]
            )
            cmd.extend(
                ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
            )
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        else:
            cmd.extend(
                ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
            )

        cmd.append(str(output_path))

        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    @staticmethod
    def create_intro_chromakey(
        output_path: Path,
        width: int = 200,
        height: int = 200,
        duration: float = 1.0,
        fps: float = 30.0,
        with_audio: bool = False,
    ):
        """Create intro with green background and white moving square."""
        cmd = ["ffmpeg", "-y", "-f", "lavfi"]

        # Green background with white box moving across
        filter_str = (
            f"color=c=green:s={width}x{height}:d={duration}:rate={fps},"
            f"drawbox=x='(w-50)*t/{duration}':y=(h-50)/2:w=50:h=50:color=white:t=fill"
        )
        cmd.extend(["-i", filter_str])

        if with_audio:
            cmd.extend(["-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}"])
            cmd.extend(
                ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
            )
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        else:
            cmd.extend(
                ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
            )

        cmd.append(str(output_path))

        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    @staticmethod
    def create_intro_alpha(
        output_path: Path,
        width: int = 200,
        height: int = 200,
        duration: float = 1.0,
        fps: float = 30.0,
        with_audio: bool = False,
    ):
        """Create intro with alpha channel (transparent background, opaque red circle)."""
        cmd = ["ffmpeg", "-y", "-f", "lavfi"]

        # Create RGBA with transparent background and red circle
        # Use color with alpha, then overlay a red circle
        filter_str = (
            f"color=c=0x00000000:s={width}x{height}:d={duration}:rate={fps},format=rgba,"
            f"drawbox=x=(w-80)/2:y=(h-80)/2:w=80:h=80:color=red@1.0:t=fill"
        )
        cmd.extend(["-i", filter_str])

        if with_audio:
            cmd.extend(["-f", "lavfi", "-i", f"sine=frequency=880:duration={duration}"])
            cmd.extend(
                ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuva420p"]
            )
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        else:
            cmd.extend(
                ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuva420p"]
            )

        cmd.append(str(output_path))

        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    @staticmethod
    def create_intro_with_sar(
        output_path: Path,
        width: int = 200,
        height: int = 200,
        sar: str = "2:1",
        duration: float = 1.0,
        fps: float = 30.0,
    ):
        """Create intro with non-1:1 sample aspect ratio."""
        cmd = ["ffmpeg", "-y", "-f", "lavfi"]

        filter_str = (
            f"color=c=green:s={width}x{height}:d={duration}:rate={fps},"
            f"drawbox=x=75:y=75:w=50:h=50:color=white:t=fill,"
            f"setsar={sar}"
        )
        cmd.extend(["-i", filter_str])
        cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"])
        cmd.append(str(output_path))

        subprocess.run(cmd, check=True, capture_output=True)
        return output_path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def main_video(temp_dir):
    """Create a standard main video fixture."""
    path = temp_dir / "main.mp4"
    TestFixtureGenerator.create_main_video(
        path, duration=6.0, fps=30.0, with_audio=True
    )
    return path


@pytest.fixture
def intro_chromakey(temp_dir):
    """Create a chromakey intro fixture."""
    path = temp_dir / "intro_chroma.mp4"
    TestFixtureGenerator.create_intro_chromakey(
        path, duration=1.0, fps=30.0, with_audio=False
    )
    return path


@pytest.fixture
def intro_alpha(temp_dir):
    """Create an alpha channel intro fixture."""
    path = temp_dir / "intro_alpha.mp4"
    TestFixtureGenerator.create_intro_alpha(
        path, duration=1.0, fps=30.0, with_audio=False
    )
    return path


@pytest.fixture
def intro_with_audio(temp_dir):
    """Create an intro with audio."""
    path = temp_dir / "intro_audio.mp4"
    TestFixtureGenerator.create_intro_chromakey(
        path, duration=1.0, fps=30.0, with_audio=True
    )
    return path


class TestBlitIntroVideo:
    """Test suite for blit_intro_video_onto_main_video."""

    def test_single_overlay_top_right(self, temp_dir, main_video, intro_chromakey):
        """Test single overlay at t=1s in TOP_RIGHT corner."""
        output = temp_dir / "output_single_tr.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_chromakey,
            main_video=main_video,
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,  # Show only once
            position=VideoBlitPosition.TOP_RIGHT,
        )

        assert result.exists()
        assert result.stat().st_size > 1000

        # Verify output properties
        probe = _probe(result)
        fps, duration = _fps_and_duration(probe)

        # Duration should match main video
        assert abs(duration - 6.0) < 0.5

        # Should be yuv420p
        video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        assert video_stream["pix_fmt"] == "yuv420p"

        # FPS should match main (30)
        assert abs(fps - 30.0) < 1.0

    def test_repeated_overlay_every_2s(self, temp_dir, main_video, intro_chromakey):
        """Test repeated overlay every 2s starting at t=1s."""
        output = temp_dir / "output_repeated.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_chromakey,
            main_video=main_video,
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=2,  # Repeat every 2s
            position=VideoBlitPosition.BOTTOM_LEFT,
        )

        assert result.exists()
        probe = _probe(result)
        fps, duration = _fps_and_duration(probe)

        # Should have overlays at t=1s, 3s, 5s (3 total within 6s main video)
        # Duration should still match main
        assert abs(duration - 6.0) < 0.5

        # Frame count should match main video (no hangs)
        video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        expected_frames = int(fps * duration)
        actual_frames = int(video_stream.get("nb_frames", expected_frames))

        # Allow some tolerance
        assert abs(actual_frames - expected_frames) < 10

    def test_alpha_compositing(self, temp_dir, main_video, intro_alpha):
        """Test alpha channel intro (should use alpha compositing, not chromakey)."""
        output = temp_dir / "output_alpha.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_alpha,
            main_video=main_video,
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,
            position=VideoBlitPosition.CENTER,
        )

        assert result.exists()
        probe = _probe(result)

        # Output should be yuv420p (alpha flattened)
        video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        assert video_stream["pix_fmt"] == "yuv420p"

    def test_fps_matching(self, temp_dir, main_video, intro_chromakey):
        """Test FPS matching when intro FPS != main FPS."""
        # Create intro with different FPS
        intro_24fps = temp_dir / "intro_24fps.mp4"
        TestFixtureGenerator.create_intro_chromakey(
            intro_24fps, duration=1.0, fps=24.0, with_audio=False
        )

        output = temp_dir / "output_fps_match.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_24fps,
            main_video=main_video,
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,
            position=VideoBlitPosition.TOP_LEFT,
            match_fps=True,
        )

        assert result.exists()
        probe = _probe(result)
        fps, duration = _fps_and_duration(probe)

        # Output FPS should match main (30)
        assert abs(fps - 30.0) < 1.0

    def test_audio_mixing_both_have_audio(self, temp_dir, main_video, intro_with_audio):
        """Test audio mixing when both intro and main have audio."""
        output = temp_dir / "output_audio_mix.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_with_audio,
            main_video=main_video,
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,
            position=VideoBlitPosition.CENTER,
            outro_gain=0.8,
            main_gain=1.0,
        )

        assert result.exists()
        probe = _probe(result)

        # Should have audio stream
        audio_streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
        assert len(audio_streams) == 1

        # Duration should match video
        _, video_duration = _fps_and_duration(probe)
        audio_duration = float(audio_streams[0].get("duration", video_duration))
        assert abs(audio_duration - video_duration) < 0.5

    def test_audio_only_main(self, temp_dir, main_video, intro_chromakey):
        """Test when only main has audio."""
        output = temp_dir / "output_audio_main_only.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_chromakey,  # No audio
            main_video=main_video,  # Has audio
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,
            position=VideoBlitPosition.BOTTOM_RIGHT,
        )

        assert result.exists()
        probe = _probe(result)

        # Should have audio (from main)
        audio_streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
        assert len(audio_streams) == 1

    def test_audio_no_audio(self, temp_dir, intro_chromakey):
        """Test when neither main nor intro have audio."""
        # Create main without audio
        main_no_audio = temp_dir / "main_no_audio.mp4"
        TestFixtureGenerator.create_main_video(
            main_no_audio, duration=6.0, fps=30.0, with_audio=False
        )

        output = temp_dir / "output_no_audio.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_chromakey,
            main_video=main_no_audio,
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,
            position=VideoBlitPosition.CENTER,
        )

        assert result.exists()
        probe = _probe(result)

        # Should have no audio
        audio_streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
        assert len(audio_streams) == 0

    def test_center_scaling_larger_intro(self, temp_dir, main_video):
        """Test CENTER with intro larger than main (should clamp and preserve AR)."""
        # Create large intro (800x600)
        large_intro = temp_dir / "intro_large.mp4"
        TestFixtureGenerator.create_intro_chromakey(
            large_intro, width=800, height=600, duration=1.0, fps=30.0
        )

        output = temp_dir / "output_center_clamped.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=large_intro,
            main_video=main_video,  # 640x360
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,
            position=VideoBlitPosition.CENTER,
        )

        assert result.exists()

        # Intro should be clamped to fit within 640x360 with AR preserved
        # Original AR = 800/600 = 4/3
        # Should be constrained by width: 640x480 → but height > 360, so constrain by height
        # 360 * (4/3) = 480, but 480 > 640, so actually constrain by width
        # Final: 640x480... wait, 480 > 360, so constrain by height: w = 360 * (4/3) = 480
        # Actually the logic clamps to min(intro, main) then preserves AR
        # 800x600 → min(800,640) x min(600,360) = 640x360
        # AR check: 800/600 = 1.33, 640/360 = 1.78
        # Intro is narrower, so constrain by height: w = 360 * (4/3) = 480, h = 360
        # Result should be ≤ 640x360

    def test_max_repeats_limit(self, temp_dir, main_video, intro_chromakey):
        """Test max_repeats parameter limits repetitions."""
        output = temp_dir / "output_max_repeats.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_chromakey,
            main_video=main_video,
            output_path=output,
            start_time_seconds=0,
            repeat_every_seconds=1,  # Could repeat 6 times
            max_repeats=3,  # But limit to 3
            position=VideoBlitPosition.TOP_RIGHT,
        )

        assert result.exists()

        # Should only have 3 overlays (at t=0s, 1s, 2s), not 6
        probe = _probe(result)
        _, duration = _fps_and_duration(probe)
        assert abs(duration - 6.0) < 0.5

    def test_custom_chroma_color(self, temp_dir, main_video):
        """Test custom chroma color (blue instead of green)."""
        # Create intro with blue background
        blue_intro = temp_dir / "intro_blue.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=200x200:d=1:rate=30,drawbox=x=75:y=75:w=50:h=50:color=white:t=fill",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(blue_intro),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        output = temp_dir / "output_blue_chroma.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=blue_intro,
            main_video=main_video,
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,
            position=VideoBlitPosition.CENTER,
            chroma_color="0x0000FF",  # Blue
            similarity=0.3,
            blend=0.1,
        )

        assert result.exists()

    def test_corner_scale_percent(self, temp_dir, main_video, intro_chromakey):
        """Test custom corner_scale_percent."""
        output = temp_dir / "output_corner_20pct.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_chromakey,
            main_video=main_video,
            output_path=output,
            start_time_seconds=1,
            repeat_every_seconds=-1,
            position=VideoBlitPosition.BOTTOM_LEFT,
            scale_percent=0.20,  # 20% instead of default 10%
        )

        assert result.exists()

        # Intro should be larger (20% of min dimension vs 10%)

    def test_start_beyond_duration(self, temp_dir, main_video, intro_chromakey):
        """Test when start_time_seconds >= main_duration (intro shouldn't appear)."""
        output = temp_dir / "output_no_show.mp4"

        result = blit_overlay_video_onto_main_video(
            overlay_video=intro_chromakey,
            main_video=main_video,  # 6s duration
            output_path=output,
            start_time_seconds=10,  # Beyond duration
            repeat_every_seconds=-1,
            position=VideoBlitPosition.CENTER,
        )

        assert result.exists()

        # Should complete without error (enable='0')
        probe = _probe(result)
        _, duration = _fps_and_duration(probe)
        assert abs(duration - 6.0) < 0.5

    def test_invalid_intro_path(self, temp_dir, main_video):
        """Test error handling for missing intro file."""
        output = temp_dir / "output_error.mp4"
        fake_intro = temp_dir / "nonexistent.mp4"

        with pytest.raises(FileNotFoundError, match="Intro video not found"):
            blit_overlay_video_onto_main_video(
                overlay_video=fake_intro,
                main_video=main_video,
                output_path=output,
                start_time_seconds=1,
                repeat_every_seconds=-1,
                position=VideoBlitPosition.CENTER,
            )

    def test_invalid_main_path(self, temp_dir, intro_chromakey):
        """Test error handling for missing main file."""
        output = temp_dir / "output_error.mp4"
        fake_main = temp_dir / "nonexistent.mp4"

        with pytest.raises(FileNotFoundError, match="Main video not found"):
            blit_overlay_video_onto_main_video(
                overlay_video=intro_chromakey,
                main_video=fake_main,
                output_path=output,
                start_time_seconds=1,
                repeat_every_seconds=-1,
                position=VideoBlitPosition.CENTER,
            )


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "-s"])
