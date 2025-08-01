"""
This module contains the video workflows for ComfyUI.
"""

import os
from typing_extensions import override

from ai_video_creator.ComfyUI_automation.comfyui_workflow import ComfyUIWorkflowBase


# Get the current directory where this file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_DIR = f"{CURRENT_DIR}/workflows"


class AnimateDiffWorkflow(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    ANIMATE_DIFF_WORKFLOW_PATH = f"{WORKFLOW_DIR}/AnimateDiff_Uniform_API.json"
    POSITIVE_PROMPT_NODE_INDEX = 3
    NEGATIVE_PROMPT_NODE_INDEX = 6
    KSAMPLER_NODE_INDEX = 7
    LATENT_IMAGE_NODE_INDEX = 9
    STABLE_DIFFUSION_LOADER_NODE_INDEX = 32
    ANIMATEDIFF_LOADER_NODE_INDEX = 36
    VIDEO_COMBINE_NODE_INDEX = 37

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

    def set_animatediff_model(self, model_name: str) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """

        models_parameters = {
            self.STABLE_DIFFUSION_LOADER_NODE_INDEX: {"model_name": model_name}
        }

        super()._set_fields(models_parameters)

    @override
    def set_stable_diffusion_model(self, model_name: str) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """

        models_parameters = {
            self.STABLE_DIFFUSION_LOADER_NODE_INDEX: {"ckpt_name": model_name}
        }

        super()._set_fields(models_parameters)

    @override
    def set_models(self, model_names: list[str]) -> None:
        """
        Set the Animatediff model.
        """
        assert len(model_names) >= 2, "Two model names are required."
        self.set_stable_diffusion_model(model_names[0])
        self.set_animatediff_model(model_names[1])

    def set_ksampler(
        self,
        seed: int,
        steps: int,
        cfg: int,
        sampler_name: str,
        scheduler: str,
        denoise: float,
    ) -> None:
        """
        Set the ksamper sweeper to the JSON configuration.
        """
        parameters = {
            self.KSAMPLER_NODE_INDEX: {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": denoise,
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
            self.KSAMPLER_NODE_INDEX: {
                "positive_prompt": positive_prompt,
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
            self.KSAMPLER_NODE_INDEX: {
                "negative_prompt": negative_prompt,
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
            self.LATENT_IMAGE_NODE_INDEX: {
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
            self.LATENT_IMAGE_NODE_INDEX: {
                "batch_size": batch_size,
            }
        }
        super()._set_fields(parameters)

    def set_latent_image(
        self,
        resolution: tuple[int, int],
        batch_size: int,
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        self.set_image_resolution(resolution)
        self.set_batch_size(batch_size)

    @override
    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """
        parameters = {
            self.VIDEO_COMBINE_NODE_INDEX: {
                "filename_prefix": filename,
            }
        }
        super()._set_fields(parameters)
