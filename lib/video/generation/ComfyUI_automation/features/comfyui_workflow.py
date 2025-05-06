"""
ComfyUI workflow automation module.
"""

from abc import ABC, abstractmethod


class IComfyUIWorkflow(ABC):
    """
    Interface for ComfyUI workflow automation.
    """

    @abstractmethod
    def set_animatediff_model(self, model_name: str) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """

    @abstractmethod
    def set_stable_diffusion_model(self, model_name: str) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """

    @abstractmethod
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

    @abstractmethod
    def set_positive_prompt(
        self,
        positive_prompt: str,
    ) -> None:
        """
        Set the positive prompt sweeper to the JSON configuration.
        """

    @abstractmethod
    def set_negative_prompt(
        self,
        negative_prompt: str,
    ) -> None:
        """
        Set the negative prompt sweeper to the JSON configuration.
        """

    @abstractmethod
    def set_latent_image(
        self,
        resolution: tuple[int, int],
        batch_size: int,
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """

    @abstractmethod
    def set_output_filename(self, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """
        
    @abstractmethod
    def get_json(self) -> dict:
        """
        Get the JSON configuration.
        """


class ComfyUIWorkflowBase:
    """
    Base class for ComfyUI
    """

    def __init__(self, base_workflow: dict):
        """
        Initialize the ComfyUIWorkflowBase class.
        """
        self.workflow = base_workflow

    def _set_animatediff_model(
        self, animatediff_loader_node_index: int, model_name: str
    ) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """

        index_str = f"{animatediff_loader_node_index}"

        self.workflow[index_str]["inputs"]["model_name"] = model_name

    def _set_stable_diffusion_model(
        self, stable_diffusion_loader_node_index: int, model_name: str
    ) -> None:
        """
        Set the model sweeper to the JSON configuration.
        """
        index_str = f"{stable_diffusion_loader_node_index}"

        self.workflow[index_str]["inputs"]["ckpt_name"] = model_name

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
        index_str = f"{ksampler_node_index}"

        self.workflow[index_str]["inputs"]["seed"] = seed
        self.workflow[index_str]["inputs"]["steps"] = steps
        self.workflow[index_str]["inputs"]["cfg"] = cfg
        self.workflow[index_str]["inputs"]["sampler_name"] = sampler_name
        self.workflow[index_str]["inputs"]["scheduler"] = scheduler
        self.workflow[index_str]["inputs"]["denoise"] = denoise

    def _set_positive_prompt(
        self,
        positive_prompt_node_index: int,
        positive_prompt: str,
    ) -> None:
        """
        Set the positive prompt sweeper to the JSON configuration.
        """
        index_str = f"{positive_prompt_node_index}"

        self.workflow[index_str]["inputs"]["text"] = positive_prompt

    def _set_negative_prompt(
        self,
        negative_prompt_node_index: int,
        negative_prompt: str,
    ) -> None:
        """
        Set the negative prompt sweeper to the JSON configuration.
        """
        index_str = f"{negative_prompt_node_index}"

        self.workflow[index_str]["inputs"]["text"] = negative_prompt

    def _set_latent_image(
        self,
        latent_image_node_index: int,
        resolution: tuple[int, int],
        batch_size: int,
    ) -> None:
        """
        Set the batch size sweeper to the JSON configuration.
        """
        index_str = f"{latent_image_node_index}"

        self.workflow[index_str]["inputs"]["width"] = resolution[0]
        self.workflow[index_str]["inputs"]["height"] = resolution[1]
        self.workflow[index_str]["inputs"]["batch_size"] = batch_size

    def _set_output_filename(self, output_node_index: int, filename: str) -> None:
        """
        Set the output filename for the generated image.
        """
        index_str = f"{output_node_index}"

        self.workflow[index_str]["inputs"]["filename_prefix"] = filename

    def get_json(self) -> dict:
        """
        Get the JSON configuration.
        """
        return self.workflow
