"""
This module contains the video workflows for ComfyUI.
"""

import os
import random
from typing_extensions import override

from ai_video_creator.comfyui.comfyui_workflow import ComfyUIWorkflowBase

# Get the current directory where this file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_DIR = f"{CURRENT_DIR}/workflows"


class StableDiffusionWorkflowBase(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    def __init__(self, base_workflow: dict) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(base_workflow=base_workflow)

    def _set_stable_diffusion_model(self, stable_diffusion_node_index: int, model_name: str) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """

        models_parameters = {stable_diffusion_node_index: {"ckpt_name": model_name}}

        super()._set_fields(models_parameters)
        workflow_summary = f"StableDiffusionModel({model_name})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_models(self, model_index: list[int], model_names: list[str]) -> None:
        """
        Set the Animatediff model.
        """
        assert len(model_names) >= 1, "Two model names are required."
        assert len(model_index) >= 1, "Two model names are required."
        assert len(model_index) == len(model_names), "Model index and names must match."
        self._set_stable_diffusion_model(model_index[0], model_names[0])

    def _set_ksampler(
        self,
        ksampler_node_index: int,
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
            ksampler_node_index: {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": denoise,
            }
        }
        super()._set_fields(parameters)
        workflow_summary = f"KSampler[seed({seed}),steps({steps}),cfg({cfg}),sampler({sampler_name}),scheduler({scheduler}),denoise({denoise})]/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_positive_prompt(
        self,
        positive_prompt_node_index: int,
        positive_prompt: str,
    ) -> None:
        """
        Set the positive prompt sweeper to the JSON configuration.
        """

        parameters = {
            positive_prompt_node_index: {
                "text": positive_prompt,
            }
        }
        super()._set_fields(parameters)
        pp_list = positive_prompt.split(" ")
        while len(pp_list) < 2:
            pp_list.append("'Empty'")
        workflow_summary = f"PositivePrompt({pp_list[0]} {pp_list[1]}...)/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_negative_prompt(
        self,
        negative_prompt_node_index: int,
        negative_prompt: str,
    ) -> None:
        """
        Set the negative prompt sweeper to the JSON configuration.
        """
        parameters = {
            negative_prompt_node_index: {
                "text": negative_prompt,
            }
        }
        super()._set_fields(parameters)
        np_list = negative_prompt.split(" ")
        workflow_summary = f"NegativePrompt({np_list[0]} {np_list[1]}...)/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_image_resolution(
        self,
        latent_image_node_index: int,
        resolution: tuple[int, int],
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        parameters = {
            latent_image_node_index: {
                "width": resolution[0],
                "height": resolution[1],
            }
        }
        super()._set_fields(parameters)
        workflow_summary = f"Resolution({resolution[0]},{resolution[1]})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_batch_size(
        self,
        latent_image_node_index: int,
        batch_size: int,
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        parameters = {
            latent_image_node_index: {
                "batch_size": batch_size,
            }
        }
        super()._set_fields(parameters)
        workflow_summary = f"BatchSize({batch_size})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_latent_image(
        self,
        latent_image_node_index: int,
        resolution: tuple[int, int],
        batch_size: int,
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        self._set_image_resolution(latent_image_node_index, resolution)
        self._set_batch_size(latent_image_node_index, batch_size)

    def _set_output_filename(self, output_file_node_index: int, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """
        parameters = {
            output_file_node_index: {
                "filename_prefix": filename,
            }
        }
        super()._set_fields(parameters)
        workflow_summary = f"{'/'.join(self.get_workflow_summary().split('/')[:-1])}/{filename}"
        self._set_workflow_summary(workflow_summary)


class StableDiffusionWorkflow(StableDiffusionWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    STABLE_DIFFUSION_WORKFLOW_PATH = f"{CURRENT_DIR}/workflows/StableDiffusion1.5_API.json"
    POSITIVE_PROMPT_NODE_INDEX = 13
    NEGATIVE_PROMPT_NODE_INDEX = 14
    KSAMPLER_NODE_INDEX = 15
    LATENT_IMAGE_NODE_INDEX = 18
    STABLE_DIFFUSION_LOADER_NODE_INDEX = 12
    SAVE_IMAGE_NODE_INDEX = 17

    def __init__(self, load_default_config: bool = False) -> None:
        """
        Initialize the StableDiffusionWorkflow class.
        """
        super().__init__(self.STABLE_DIFFUSION_WORKFLOW_PATH)

        # Loading default configurations for the workflow
        if load_default_config:
            self._load_default_configurations()

    def _load_default_configurations(self) -> None:
        self.set_latent_image([1024, 768], 1)
        self.set_ksampler(
            seed=random.randint(0, 2**31 - 1),
            steps=25,
            cfg=7.5,
            sampler_name="dpmpp_sde",
            scheduler="karras",
            denoise=1,
        )

    def set_stable_diffusion_model(self, model_name: str) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """
        super()._set_stable_diffusion_model(self.STABLE_DIFFUSION_LOADER_NODE_INDEX, model_name)

    def set_models(self, model_names: list[str]) -> None:
        """
        Set the Animatediff model.
        """
        super()._set_models(
            model_index=[self.STABLE_DIFFUSION_LOADER_NODE_INDEX],
            model_names=model_names,
        )

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
        super()._set_ksampler(
            self.KSAMPLER_NODE_INDEX,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            denoise=denoise,
        )

    def set_positive_prompt(
        self,
        positive_prompt: str,
    ) -> None:
        """
        Set the positive prompt sweeper to the JSON configuration.
        """
        super()._set_positive_prompt(self.POSITIVE_PROMPT_NODE_INDEX, positive_prompt)

    def set_negative_prompt(
        self,
        negative_prompt: str,
    ) -> None:
        """
        Set the negative prompt sweeper to the JSON configuration.
        """
        super()._set_negative_prompt(self.NEGATIVE_PROMPT_NODE_INDEX, negative_prompt)

    def set_image_resolution(
        self,
        resolution: tuple[int, int],
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        super()._set_image_resolution(self.LATENT_IMAGE_NODE_INDEX, resolution=resolution)

    def set_batch_size(
        self,
        batch_size: int,
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        super()._set_batch_size(self.LATENT_IMAGE_NODE_INDEX, batch_size=batch_size)

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
        super()._set_output_filename(output_file_node_index=self.SAVE_IMAGE_NODE_INDEX, filename=filename)


class UnetWorkflowBase(ComfyUIWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    def __init__(self, base_workflow: str):
        """
        Initialize the FluxWorkflow class.
        """
        super().__init__(base_workflow)

    def _set_dual_clip_loader(self, node_index: int, clip_name1: str, clip_name2: str) -> None:
        """
        Set the dual clip loader.
        """
        models_parameters = {
            node_index: {
                "clip_name1": clip_name1,
                "clip_name2": clip_name2,
            }
        }

        super()._set_fields(models_parameters)
        workflow_summary = f"DualClipLoader({clip_name1},{clip_name2})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_unet_model(self, node_index: int, model_name: str) -> None:
        """
        Set the unet model to the JSON configuration.
        """
        models_parameters = {node_index: {"unet_name": model_name}}

        super()._set_fields(models_parameters)
        workflow_summary = f"UNetModel({model_name})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_models(self, node_index: int, model_names: list[str]) -> None:
        """
        Set the Stable Diffusion model.
        """
        assert len(model_names) >= 3, "Two model names are required."
        assert len(node_index) >= 3, "Two model names are required."
        assert len(node_index) == len(model_names), "Model index and names must match."

        self._set_unet_model(node_index, model_names[0])
        self._set_dual_clip_loader(node_index, model_names[1], model_names[2])

    def _set_lora(self, node_index: int, lora_name) -> None:
        """
        Set the LoRA model to the JSON configuration.
        """
        parameters = {
            node_index: {
                "lora_name": lora_name,
            }
        }
        super()._set_fields(parameters)
        workflow_summary = f"LoRA({lora_name})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_positive_prompt(self, node_index: int, positive_prompt: str) -> None:
        """
        Set the positive prompt.
        """
        parameters = {
            node_index: {
                "string": positive_prompt,
            }
        }
        super()._set_fields(parameters)
        pp_list = positive_prompt.split(" ")
        while len(pp_list) < 2:
            pp_list.append("'Empty'")
        workflow_summary = f"PositivePrompt({pp_list[0]} {pp_list[1]}...)/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_output_filename(self, node_index: int, filename: str) -> None:
        """
        Set the output filename.
        """
        parameters = {
            node_index: {
                "filename_prefix": filename,
            }
        }
        super()._set_fields(parameters)

    def _set_image_resolution(self, width_node_index: int, height_node_index: int, width: int, height: int) -> None:
        """
        Set the image resolution.
        """
        parameters = {
            width_node_index: {
                "int": width,
            },
            height_node_index: {
                "int": height,
            },
        }
        super()._set_fields(parameters)

        workflow_summary = f"Resolution({width},{height})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_random_noise(self, node_index: int, random_noise: int) -> None:
        """
        Set the random noise.
        """
        parameters = {
            node_index: {
                "noise_seed": random_noise,
            }
        }
        super()._set_fields(parameters)

        workflow_summary = f"RandomNoise({random_noise})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)

    def _set_batch_size(self, node_index: int, batch_size: int) -> None:
        """
        Set the batch size.
        """
        parameters = {
            node_index: {
                "batch_size": batch_size,
            }
        }
        super()._set_fields(parameters)

        workflow_summary = f"BatchSize({batch_size})/{self.get_workflow_summary()}"
        self._set_workflow_summary(workflow_summary)


class FluxWorkflow(UnetWorkflowBase):
    """
    Class to handle the workflow for Stable Diffusion in ComfyUI.
    """

    FLUX_WORKFLOW_PATH = f"{WORKFLOW_DIR}/FLUX.1_API.json"
    SAVE_IMAGE_NODE_INDEX = 9
    DUAL_CLIP_NODE_INDEX = 11
    UNET_MODEL_NODE_INDEX = 12
    LORA_REWIRE_NODE_INDEX = 61
    LORA_NODE_INDEX = 73
    RANDOM_NOISE_NODE_INDEX = 25
    POSITIVE_PROMPT_NODE_INDEX = 28
    WIDTH_NODE_INDEX = 70
    HEIGHT_NODE_INDEX = 71
    BATCH_SIZE_NODE_INDEX = 5

    def __init__(self, load_default_config: bool = False) -> None:
        """
        Initialize the FluxWorkflow class.
        """
        super().__init__(self.FLUX_WORKFLOW_PATH)

        # Loading default configurations for the workflow
        if load_default_config:
            self._load_default_configurations()

    def _load_default_configurations(self) -> None:
        self.set_seed(random.randint(0, 2**31 - 1))
        self.set_lora("")
        self.set_output_filename("output")
        self.set_image_resolution((832, 480))

    def _enable_lora(self) -> None:
        """
        Enable LoRA (Low-Rank Adaptation) for the model.
        """
        self._rewire_node(
            self.LORA_REWIRE_NODE_INDEX,
            self.UNET_MODEL_NODE_INDEX,
            self.LORA_NODE_INDEX,
        )

    def _disable_lora(self) -> None:
        """
        Disable LoRA (Low-Rank Adaptation) for the model.
        """
        self._rewire_node(
            self.LORA_REWIRE_NODE_INDEX,
            self.LORA_NODE_INDEX,
            self.UNET_MODEL_NODE_INDEX,
        )

    def set_unet_model(self, model_name: str) -> None:
        """
        Set the unet model to the JSON configuration.
        """
        super()._set_unet_model(self.UNET_MODEL_NODE_INDEX, model_name)

    def set_dual_clip_loader(self, clip_name1: str, clip_name2: str) -> None:
        """
        Set the dual clip loader.
        """
        super()._set_dual_clip_loader(self.DUAL_CLIP_NODE_INDEX, clip_name1=clip_name1, clip_name2=clip_name2)

    def set_models(self, model_names: list[str]) -> None:
        """
        Set the Stable Diffusion model.
        """
        assert len(model_names) >= 3, "Two model names are required."
        self.set_unet_model(model_names[0])
        self.set_dual_clip_loader(model_names[1], model_names[2])

    def set_lora(self, lora_name: str) -> None:
        """
        Set the LoRA model.
        """
        if lora_name:
            self._enable_lora()
            super()._set_lora(self.LORA_NODE_INDEX, lora_name)
        else:
            self._disable_lora()

    def set_positive_prompt(
        self,
        positive_prompt: str,
    ) -> None:
        """
        Set the positive prompt.
        """
        super()._set_positive_prompt(self.POSITIVE_PROMPT_NODE_INDEX, positive_prompt)

    def set_image_resolution(
        self,
        width: int,
        height: int,
    ) -> None:
        """
        Set the image resolution.
        """
        super()._set_image_resolution(self.WIDTH_NODE_INDEX, self.HEIGHT_NODE_INDEX, width=width, height=height)

    def set_seed(
        self,
        random_noise: int,
    ) -> None:
        """
        Set the random noise.
        """
        super()._set_random_noise(self.RANDOM_NOISE_NODE_INDEX, random_noise=random_noise)

    def set_batch_size(self, batch_size: int) -> None:
        """
        Set the batch size.
        """
        super()._set_batch_size(self.BATCH_SIZE_NODE_INDEX, batch_size)

    @override
    def set_output_filename(self, filename):
        """
        Set the output filename.
        """
        super()._set_output_filename(self.SAVE_IMAGE_NODE_INDEX, filename)
