"""
Stable Diffusion Workflow for ComfyUI Automation
"""

import json

from typing_extensions import override

from .features.environment_variables import WORKFLOW_JSON_DIR
from .features.comfyui_workflow import IComfyUIWorkflow, ComfyUIWorkflowBase


class AnimateDiffWorkflow(IComfyUIWorkflow, ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    ANIMATE_DIFF_WORKFLOW_PATH = f"{WORKFLOW_JSON_DIR}/AnimateDiff_Uniform_API.json"
    POSITIVE_PROMPT_NODE_INDEX = 3
    NEGATIVE_PROMPT_NODE_INDEX = 6
    KSAMPLER_NODE_INDEX = 7
    LATENT_IMAGE_NODE_INDEX = 9
    STABLE_DIFFUSION_LOADER_NODE_INDEX = 32
    ANIMATEDIFF_LOADER_NODE_INDEX = 36
    VIDEO_COMBINE_NODE_INDEX = 37

    def __init__(self) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        with open(self.ANIMATE_DIFF_WORKFLOW_PATH, "r", encoding="utf-8") as file:
            workflow = json.load(file)

        super().__init__(workflow)

    @override
    def set_animatediff_model(self, model_name: str) -> None:
        """
        Set the Animatediff model.
        """
        super()._set_animatediff_model(
            self.STABLE_DIFFUSION_LOADER_NODE_INDEX, model_name
        )

    @override
    def set_stable_diffusion_model(self, model_name: str) -> None:
        """
        Set the Stable Diffusion model.
        """
        super()._set_stable_diffusion_model(
            self.STABLE_DIFFUSION_LOADER_NODE_INDEX, model_name
        )

    @override
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
        Configure the ksampler settings.
        """
        super()._set_ksampler(
            self.KSAMPLER_NODE_INDEX,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            denoise=denoise,
        )
 
    @override
    def set_positive_prompt(self, positive_prompt: str) -> None:
        """
        Set the positive prompt.
        """
        super()._set_positive_prompt(self.POSITIVE_PROMPT_NODE_INDEX, positive_prompt)

    @override
    def set_negative_prompt(self, negative_prompt: str) -> None:
        """
        Set the negative prompt.
        """
        super()._set_negative_prompt(self.NEGATIVE_PROMPT_NODE_INDEX, negative_prompt)

    @override
    def set_latent_image(self, resolution: tuple[int, int], batch_size: int) -> None:
        """
        Set the latent image.
        """
        super()._set_latent_image(self.LATENT_IMAGE_NODE_INDEX, resolution, batch_size)

    @override
    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename.
        """
        super()._set_output_filename(self.VIDEO_COMBINE_NODE_INDEX, filename)

    @override
    def get_json(self):
        return super().get_json()
