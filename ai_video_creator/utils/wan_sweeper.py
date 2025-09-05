"""
Simple Parameter Sweeper Usage Examples

Demonstrates the simplified implementation with a clean, direct interface.
"""

from logging_utils import logger, begin_console_logging, remove_default_logger

from ai_video_creator.ComfyUI_automation.comfyui_sweepers import ComfyUIParameterSweeper

from ai_video_creator.generators.ComfyUI_automation.comfyui_video_workflows import (
    WanWorkflow,
)
from ai_video_creator.ComfyUI_automation.comfyui_requests import ComfyUIRequests


def wan_sweeper():
    """Demonstrate grid sweep functionality."""

    logger.info("\n=== Grid Sweep ===\n")

    sweeper = ComfyUIParameterSweeper()

    # Test all combinations of width, height, and method
    results = sweeper.grid_sweep(
        WanWorkflow(),
        "set_params",
        steps_low=[4, 7],
        steps_high=[4, 7],
        cfg_low=[1.0, 1.2],
        cfg_high=[1.0, 1.2],
        lora_strength_low=[1.0, 1.5],
        lora_strength_high=[1.0, 1.2],
        resolution=[(640, 640)],
        seed_high=[12345],
        batch_size=[1],
        scheduler_high=["simple"],
        sampler_high=["euler"],
        fps=[12],
        frame_count=[49],
        output_filename=["12fps-49frames/euler-simple/640x640"],
    )

    extracted_workflows = [r.result for r in results if r.success]
    if not extracted_workflows:
        logger.error("No successful workflow generations.")
        return

    logger.info(f"Grid sweep generated {len(extracted_workflows)} combinations.")

    requests = ComfyUIRequests()
    requests.comfyui_ensure_send_all_prompts(extracted_workflows)


if __name__ == "__main__":
    remove_default_logger()
    with begin_console_logging("ComfyUISweeper"):
        wan_sweeper()
