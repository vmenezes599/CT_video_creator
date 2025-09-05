"""
Simple Parameter Sweeper Usage Examples

Demonstrates the simplified implementation with a clean, direct interface.
"""

import time

from ai_video_creator.ComfyUI_automation.comfyui_sweepers import ComfyUIParameterSweeper


# Example classes to demonstrate parameter sweeping
class ImageProcessor:
    """Example image processing class."""

    def __init__(self, gpu_enabled: bool = True):
        self.gpu_enabled = gpu_enabled

    def resize(self, width: int, height: int, method: str = "bilinear") -> str:
        """Resize image with given parameters."""
        time.sleep(0.1)  # Simulate processing
        gpu_suffix = " (GPU)" if self.gpu_enabled else " (CPU)"
        return f"Resized to {width}x{height} using {method}{gpu_suffix}"

    def apply_filter(self, filter_name: str, strength: float = 1.0) -> str:
        """Apply filter to image."""
        time.sleep(0.05)
        return f"Applied {filter_name} filter with strength {strength}"


class AudioProcessor:
    """Example audio processing class."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def normalize_audio(self, target_db: float = -12.0) -> str:
        """Normalize audio to target dB."""
        time.sleep(0.08)
        return f"Normalized audio to {target_db} dB @ {self.sample_rate}Hz"

    def apply_reverb(self, room_size: float, decay_time: float) -> str:
        """Apply reverb effect."""
        time.sleep(0.12)
        return f"Applied reverb: room_size={room_size}, decay_time={decay_time}s"


def example_basic_usage():
    """Demonstrate basic parameter sweeping."""

    print("=== Basic Parameter Sweeping ===\n")

    sweeper = ComfyUIParameterSweeper()

    # Test ImageProcessor with different resize parameters
    resize_params = [
        {"width": 800, "height": 600, "method": "bilinear"},
        {"width": 1024, "height": 768, "method": "bicubic"},
        {"width": 1920, "height": 1080, "method": "bilinear"},
    ]

    results = sweeper.sweep(ImageProcessor(), "resize", resize_params)

    print("Resize test results:")
    for result in results:
        print(f"  {result}")

    # Test AudioProcessor
    audio_params = [{"target_db": -6.0}, {"target_db": -12.0}, {"target_db": -18.0}]

    audio_results = sweeper.sweep(AudioProcessor(), "normalize_audio", audio_params)

    print("\nAudio normalization results:")
    for result in audio_results:
        print(f"  {result}")

    # Get summary
    all_results = results + audio_results
    summary = sweeper.get_summary(all_results)
    print(
        f"\nSummary: {summary['successful']}/{summary['total']} successful "
        f"({summary['success_rate']:.1%} success rate)"
    )


def example_grid_sweep():
    """Demonstrate grid sweep functionality."""

    print("\n=== Grid Sweep ===\n")

    sweeper = ComfyUIParameterSweeper()

    # Test all combinations of width, height, and method
    results = sweeper.grid_sweep(
        ImageProcessor(),
        "resize",
        width=[800, 1024],
        height=[600, 768],
        method=["bilinear", "bicubic"],
    )

    print(f"Grid sweep generated {len(results)} combinations:")
    for result in results:
        if result.success:
            print(f"  ✓ {result.parameters} -> {result.execution_time:.3f}s")

    # Find fastest combination
    successful = [r for r in results if r.success]
    if successful:
        fastest = min(successful, key=lambda r: r.execution_time)
        print(f"\nFastest: {fastest.parameters} ({fastest.execution_time:.3f}s)")


def example_streaming():
    """Demonstrate streaming results for memory efficiency."""

    print("\n=== Streaming Results ===\n")

    sweeper = ComfyUIParameterSweeper()

    # Generate large parameter set
    reverb_params = []
    for room_size in [0.1, 0.3, 0.5, 0.7, 0.9]:
        for decay_time in [1.0, 2.0, 3.0, 4.0]:
            reverb_params.append({"room_size": room_size, "decay_time": decay_time})

    print(f"Streaming {len(reverb_params)} parameter combinations...")

    successful_count = 0
    for result in sweeper.stream_sweep(AudioProcessor(), "apply_reverb", reverb_params):
        if result.success:
            successful_count += 1
            if result.parameters["room_size"] > 0.7:  # Log large rooms
                print(
                    f"  Large room: {result.parameters} -> {result.execution_time:.3f}s"
                )

    print(f"Completed: {successful_count} successful results")


def example_error_handling():
    """Demonstrate error handling."""

    print("\n=== Error Handling ===\n")

    sweeper = ComfyUIParameterSweeper()

    # Test with invalid parameters
    bad_params = [
        {"width": "invalid", "height": 600},  # Wrong type
        {"width": 800},  # Missing required parameter
        {"width": 800, "height": 600, "unknown_param": "test"},  # Extra parameter
    ]

    results = sweeper.sweep(ImageProcessor(), "resize", bad_params)

    print("Error handling results:")
    for result in results:
        print(f"  {result}")

    summary = sweeper.get_summary(results)
    print(
        f"\nError test summary: {summary['successful']}/{summary['total']} successful"
    )


if __name__ == "__main__":
    print("Simple Parameter Sweeper Examples")
    print("=" * 50)

    example_basic_usage()
    example_grid_sweep()
    example_streaming()
    example_error_handling()

    print("\n" + "=" * 50)
    print("Examples completed!")
