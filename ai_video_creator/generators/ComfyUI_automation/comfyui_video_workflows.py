"""
This module contains the video workflows for ComfyUI.
"""

import copy
import os
from ai_video_creator.ComfyUI_automation.comfyui_workflow import ComfyUIWorkflowBase


# Get the current directory where this file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_DIR = f"{CURRENT_DIR}/workflows"


class WanWorkflow(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    # 2 passes. High Noise with sampler and Low Noise without sampler.
    ANIMATE_DIFF_WORKFLOW_PATH = f"{WORKFLOW_DIR}/WAN2.2_FirstFrameOnly_API.json"

    CFG_LOW_NOISE_NODE_INDEX = 85
    STEPS_LOW_NOISE_NODE_INDEX = 85
    SEED_LOW_NOISE_NODE_INDEX = 85
    SAMPLER_LOW_NOISE_NODE_INDEX = 85
    SCHEDULER_LOW_NOISE_NODE_INDEX = 85

    CFG_HIGH_NOISE_NODE_INDEX = 86
    STEPS_HIGH_NOISE_NODE_INDEX = 86
    SEED_HIGH_NOISE_NODE_INDEX = 86
    SAMPLER_HIGH_NOISE_NODE_INDEX = 86
    SCHEDULER_HIGH_NOISE_NODE_INDEX = 86

    NEGATIVE_PROMPT_NODE_INDEX = 89
    POSITIVE_PROMPT_NODE_INDEX = 93

    FPS_NODE_INDEX = 94
    BATCH_SIZE_NODE_INDEX = 98
    FRAME_COUNT_NODE_INDEX = 98
    IMAGE_RESOLUTION_NODE_INDEX = 98
    LORA_HIGH_NOISE_NODE_INDEX = 101
    LORA_LOW_NOISE_NODE_INDEX = 102
    OUTPUT_FILENAME_NODE_INDEX = 108

    def __init__(self, load_best_config: bool = True) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(self.ANIMATE_DIFF_WORKFLOW_PATH)

        # Loading best configurations for the workflow
        if load_best_config:
            self._load_best_configurations()

    def _load_best_configurations(self) -> None:
        pass

    def set_steps_low_noise(
        self,
        steps: int,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.STEPS_LOW_NOISE_NODE_INDEX: {
                "steps": steps,
            }
        }
        super()._set_fields(parameters)

    def set_steps_high_noise(
        self,
        steps: int,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.STEPS_HIGH_NOISE_NODE_INDEX: {
                "steps": steps,
            }
        }
        super()._set_fields(parameters)

    def set_cfg_low_noise(
        self,
        cfg: float,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.CFG_LOW_NOISE_NODE_INDEX: {
                "cfg": cfg,
            }
        }
        super()._set_fields(parameters)

    def set_cfg_high_noise(
        self,
        cfg: int,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.CFG_HIGH_NOISE_NODE_INDEX: {
                "cfg": cfg,
            }
        }
        super()._set_fields(parameters)

    def set_sampler_low_noise(
        self,
        sampler: str,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.SAMPLER_LOW_NOISE_NODE_INDEX: {
                "sampler_name": sampler,
            }
        }
        super()._set_fields(parameters)

    def set_sampler_high_noise(
        self,
        sampler: str,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.SAMPLER_HIGH_NOISE_NODE_INDEX: {
                "sampler_name": sampler,
            }
        }
        super()._set_fields(parameters)

    def set_scheduler_low_noise(
        self,
        scheduler: str,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.SCHEDULER_LOW_NOISE_NODE_INDEX: {
                "scheduler": scheduler,
            }
        }
        super()._set_fields(parameters)

    def set_scheduler_high_noise(
        self,
        scheduler: str,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.SCHEDULER_HIGH_NOISE_NODE_INDEX: {
                "scheduler": scheduler,
            }
        }
        super()._set_fields(parameters)

    def set_lora_strength_low_noise(
        self,
        strength: float,
    ) -> None:
        """
        Set the LORA strength for low noise.
        """
        parameters = {
            self.LORA_LOW_NOISE_NODE_INDEX: {
                "strength_model": strength,
            }
        }
        super()._set_fields(parameters)

    def set_lora_strength_high_noise(
        self,
        strength: float,
    ) -> None:
        """
        Set the LORA strength for high noise.
        """
        parameters = {
            self.LORA_HIGH_NOISE_NODE_INDEX: {
                "strength_model": strength,
            }
        }
        super()._set_fields(parameters)

    def set_seed_high_noise(
        self,
        seed: int,
    ) -> None:
        """
        Set the seed sweeper to the JSON configuration.
        """
        parameters = {
            self.SEED_HIGH_NOISE_NODE_INDEX: {
                "noise_seed": seed,
            }
        }
        super()._set_fields(parameters)

    def set_positive_prompt(
        self,
        positive_prompt: str,
    ) -> None:
        """
        Set the positive prompt sweeper to the JSON configuration.
        """

        parameters = {
            self.POSITIVE_PROMPT_NODE_INDEX: {
                "text": positive_prompt,
            }
        }
        super()._set_fields(parameters)

    def set_negative_prompt(
        self,
        negative_prompt: str,
    ) -> None:
        """
        Set the negative prompt sweeper to the JSON configuration.
        """
        parameters = {
            self.NEGATIVE_PROMPT_NODE_INDEX: {
                "text": negative_prompt,
            }
        }
        super()._set_fields(parameters)

    def set_image_resolution(
        self,
        resolution: tuple[int, int],
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        parameters = {
            self.IMAGE_RESOLUTION_NODE_INDEX: {
                "width": resolution[0],
                "height": resolution[1],
            }
        }
        super()._set_fields(parameters)

    def set_batch_size(
        self,
        batch_size: int,
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        parameters = {
            self.BATCH_SIZE_NODE_INDEX: {
                "batch_size": batch_size,
            }
        }
        super()._set_fields(parameters)

    def set_frame_count(self, frame_count: int) -> None:
        """
        Set the frame count for the video generation.
        """
        parameters = {
            self.FRAME_COUNT_NODE_INDEX: {
                "length": frame_count,
            }
        }
        super()._set_fields(parameters)

    def set_fps(self, fps: int) -> None:
        """
        Set the frames per second (FPS) for the video generation.
        """
        parameters = {
            self.FPS_NODE_INDEX: {
                "fps": fps,
            }
        }
        super()._set_fields(parameters)

    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """
        parameters = {
            self.OUTPUT_FILENAME_NODE_INDEX: {
                "filename_prefix": filename,
            }
        }
        super()._set_fields(parameters)

    def set_params(
        self,
        resolution: tuple[int, int] | None = None,
        cfg_low: int | None = None,
        steps_low: int | None = None,
        cfg_high: float | None = None,
        steps_high: int | None = None,
        sampler_high: str | None = None,
        scheduler_high: str | None = None,
        lora_strength_high: float | None = None,
        lora_strength_low: float | None = None,
        seed_high: int | None = None,
        positive_prompt: str | None = None,
        negative_prompt: str | None = None,
        batch_size: int | None = None,
        frame_count: int | None = None,
        fps: int | None = None,
        output_filename: str | None = None,
    ) -> "WanWorkflow":
        """
        Set multiple parameters at once.
        """
        if resolution is not None:
            self.set_image_resolution(resolution)
        if cfg_low is not None:
            self.set_cfg_low_noise(cfg_low)
        if steps_low is not None:
            self.set_steps_low_noise(steps_low)
        if cfg_high is not None:
            self.set_cfg_high_noise(cfg_high)
        if steps_high is not None:
            self.set_steps_high_noise(steps_high)
        if lora_strength_high is not None:
            self.set_lora_strength_high_noise(lora_strength_high)
        if lora_strength_low is not None:
            self.set_lora_strength_low_noise(lora_strength_low)
        if sampler_high is not None:
            self.set_sampler_high_noise(sampler_high)
            self.set_sampler_low_noise(sampler_high)
        if scheduler_high is not None:
            self.set_scheduler_high_noise(scheduler_high)
            self.set_scheduler_low_noise(scheduler_high)
        if seed_high is not None:
            self.set_seed_high_noise(seed_high)
        if positive_prompt is not None:
            self.set_positive_prompt(positive_prompt)
        if negative_prompt is not None:
            self.set_negative_prompt(negative_prompt)
        if batch_size is not None:
            self.set_batch_size(batch_size)
        if frame_count is not None:
            self.set_frame_count(frame_count)
        if fps is not None:
            self.set_fps(fps)
        if output_filename is not None:
            extra_name = f"{output_filename}/res({resolution[0]}x{resolution[1]})_cfg({cfg_low}-{cfg_high})_steps({steps_low}-{steps_high})_seed({seed_high})_lora({lora_strength_low}-{lora_strength_high})"
            self.set_output_filename(extra_name)

        return copy.deepcopy(self)
