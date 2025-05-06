"""
Stable Diffusion Workflow for ComfyUI Automation
"""

import json
import random

from typing_extensions import override

from .features.environment_variables import WORKFLOW_JSON_DIR
from .features.comfyui_workflow import IComfyUIWorkflow, ComfyUIWorkflowBase


class StableDiffusionWorkflow(IComfyUIWorkflow, ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    STABLE_DIFFUSION_WORKFLOW_PATH = f"{WORKFLOW_JSON_DIR}/StableDiffusion1.5_API.json"
    POSITIVE_PROMPT_NODE_INDEX = 13
    NEGATIVE_PROMPT_NODE_INDEX = 14
    KSAMPLER_NODE_INDEX = 15
    LATENT_IMAGE_NODE_INDEX = 18
    STABLE_DIFFUSION_LOADER_NODE_INDEX = 12
    SAVE_IMAGE_NODE_INDEX = 17

    def __init__(self) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        with open(self.STABLE_DIFFUSION_WORKFLOW_PATH, "r", encoding="utf-8") as file:
            workflow = json.load(file)

        super().__init__(workflow)

        # Loading best configurations for the workflow
        self._load_best_configurations()

    def _load_best_configurations(self) -> None:
        self.set_latent_image([1024,768], 1)
        self.set_ksampler(
            seed=random.randint(0, 2**32 - 1),
            steps=25,
            cfg=7.5,
            sampler_name="dpmpp_sde",
            scheduler="karras",
            denoise=1,
        )

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
        super()._set_output_filename(output_node_index=self.SAVE_IMAGE_NODE_INDEX, filename=filename)

    @override
    def get_json(self) -> dict:
        return ComfyUIWorkflowBase.get_json(self)
