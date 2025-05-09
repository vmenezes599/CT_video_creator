"""
ComfyUI Automation Sweep Module
"""

import copy
import json
from itertools import product

from .comfyui_workflow import StableDiffusionWorkflow, IComfyUIWorkflow
from .comfyui_requests import ComfyUIRequests
from .custom_logger import logger


class ComfyUISweeperBase:
    """
    Base class for ComfyUI sweepers.
    """

    def __init__(self, comfyui_url: str) -> None:
        """
        Initialize the ComfyUISweeperBase class.
        """

        self.req_list: list[tuple[IComfyUIWorkflow, str]] = []

        self.requests = ComfyUIRequests(comfyui_url)

        # Log initialization
        logger.info("Initializing ComfyUISweep...")

    def _save_first_and_last_requests(self) -> None:
        """
        Save the first and last requests to JSON files.
        """
        total_requests = len(self.req_list)

        # Save the first request to a file
        if total_requests > 0:
            first_request = self.req_list[0]

            output_file_path = (
                f"{self.log_file_name.split('.', maxsplit=1)[0]}_first.json"
            )
            with open(output_file_path, "w", encoding="utf-8") as file:
                json.dump(first_request[0].get_json(), file, indent=4)
            logger.info("First request saved to %s", output_file_path)

        if total_requests > 2:
            last_request = self.req_list[-1]

            output_file_path = (
                f"{self.log_file_name.split('.', maxsplit=1)[0]}_last.json"
            )
            with open(output_file_path, "w", encoding="utf-8") as file:
                json.dump(last_request[0].get_json(), file, indent=4)
            logger.info("Last request saved to %s", output_file_path)

        logger.info("--------------------------------------------------")

    def _set_output_nodes(self) -> None:
        """
        Set the output node in the JSON configuration.
        """
        for req, ouput_name in self.req_list:
            req.set_output_filename(ouput_name.split("/")[-1])

    def send_requests(self):
        """
        Send a request to ComfyUI with the current configuration.
        """
        self._save_first_and_last_requests()
        self._set_output_nodes()

        self.requests.comfyui_ensure_send_all_prompts(self.req_list)


class StableDiffusionComfyUISweeper(ComfyUISweeperBase):
    """
    Class to handle the sweep of parameters for ComfyUI.
    """

    WORLFLOW_TYPE = StableDiffusionWorkflow

    def __init__(self, comfyui_url: str):
        super().__init__(comfyui_url)

        self.req_list: list[StableDiffusionWorkflow] = [self.WORLFLOW_TYPE()]

    def add_animatediff_model_sweeper(self, model_name_list: list[str]) -> None:
        """
        Add the model sweeper to the JSON configuration.
        """
        local_req_list: list[StableDiffusionWorkflow] = []
        for model_name in model_name_list:
            for req in self.req_list:
                local_prompt = copy.deepcopy(req)

                local_prompt.set_animatediff_model(model_name)

                output_model_name = model_name.split(".")[0]
                worlkflow_summary = f"{output_model_name}/{req.get_workflow_summary()}"

                local_prompt.set_workflow_summary(worlkflow_summary)
                local_req_list.append(local_prompt)

        self.req_list = local_req_list

    def add_stable_diffusion_model_sweeper(self, model_name_list: list[str]) -> None:
        """
        Add the model sweeper to the JSON configuration.
        """
        local_req_list: list[StableDiffusionWorkflow] = []
        for model_name in model_name_list:
            for req in self.req_list:
                local_prompt = copy.deepcopy(req)

                local_prompt.set_stable_diffusion_model(model_name)

                local_req_list.append(local_prompt)

        self.req_list = local_req_list

    def add_ksampler_sweeper(
        self,
        seed_list: list[int],
        steps_list: list[int],
        cfg_list: list[int],
        sampler_name_list: list[str],
        scheduler_list: list[str],
        denoise_list: list[float],
    ) -> None:
        """
        Add the ksamper sweeper to the JSON configuration.
        """
        try:
            local_req_list: list[StableDiffusionWorkflow] = []
            for req in self.req_list:
                for (
                    seed,
                    steps,
                    cfg,
                    sampler_name,
                    scheduler,
                    denoise,
                ) in product(
                    seed_list,
                    steps_list,
                    cfg_list,
                    sampler_name_list,
                    scheduler_list,
                    denoise_list,
                ):
                    local_prompt = copy.deepcopy(req)

                    local_prompt.set_ksampler(
                        seed=seed,
                        steps=steps,
                        cfg=cfg,
                        sampler_name=sampler_name,
                        scheduler=scheduler,
                        denoise=denoise,
                    )

                    local_req_list.append(local_prompt)

            self.req_list = local_req_list
        except Exception as e:
            logger.error("Error in add_ksampler_sweeper: %s", e)
            raise

    def add_positive_prompt_sweeper(
        self,
        positive_prompt_list: list[str],
    ) -> None:
        """
        Add the positive prompt sweeper to the JSON configuration.
        """
        for i, pp in enumerate(positive_prompt_list):
            logger.info("Adding positive prompt %s: %s", i, pp)
            logger.info("--------------------------------------------------")

        local_req_list: list[StableDiffusionWorkflow] = []
        for req in self.req_list:
            for i, positive_prompt in enumerate(positive_prompt_list):
                local_prompt = copy.deepcopy(req)

                local_prompt.set_positive_prompt(positive_prompt)

                local_req_list.append(local_prompt)

        self.req_list = local_req_list
        self.logger_explanation = f"{self.logger_explanation}_PositivePrompt"

    def add_negative_prompt_sweeper(
        self,
        negative_prompt_list: list[str],
    ) -> None:
        """
        Add the negative prompt sweeper to the JSON configuration.
        """
        for i, np in enumerate(negative_prompt_list):
            logger.info("Adding negative prompt %s: %s", i, np)
            logger.info("--------------------------------------------------")

        local_req_list: list[StableDiffusionWorkflow] = []
        for req in self.req_list:
            for i, negative_prompt in enumerate(negative_prompt_list):
                local_prompt = copy.deepcopy(req)

                local_prompt.set_negative_prompt(negative_prompt)

                local_req_list.append(local_prompt)

        self.req_list = local_req_list

    def add_latent_image_sweeper(
        self,
        resolution_list: list[tuple[int, int]],
        batch_size_list: list[int],
    ) -> None:
        """
        Add the batch size sweeper to the JSON configuration.
        """
        for i, bs in enumerate(batch_size_list):
            logger.info("Adding batch size %s: %s", i, bs)
            logger.info("--------------------------------------------------")

        local_req_list: list[StableDiffusionWorkflow] = []
        for req in self.req_list:
            for i, (batch_size, resolution) in enumerate(
                product(batch_size_list, resolution_list)
            ):
                local_prompt = copy.deepcopy(req)

                local_prompt.set_latent_image(
                    batch_size=batch_size, resolution=resolution
                )

                local_req_list.append(local_prompt)

        self.req_list = local_req_list
