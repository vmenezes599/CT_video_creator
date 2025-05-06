"""
ComfyUI Automation Sweep Module
"""

import copy
import json
import time
from datetime import datetime
from itertools import product
from typing import Type
from requests.exceptions import RequestException

from .comfyui_workflow import IComfyUIWorkflow
from .comfyui_helpers import comfyui_get_history_output_name
from .comfyui_requests import ComfyUIRequests
from .custom_logger import CustomLogger


class ComfyUISweep:
    """
    Class to handle the sweep of parameters for ComfyUI.
    """

    def __init__(
        self,
        comfyui_url: str,
        workflow_type: Type[IComfyUIWorkflow],
        output_folder: str = "output/",
        output_name: str = "output",
    ):
        self.workflow_type = workflow_type
        self.logger_explanation = output_name

        self.req_list: list[tuple[IComfyUIWorkflow, str]] = [
            (self.workflow_type(), output_name)
        ]

        unique_suffix = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")  # Timestamp
        self.log_file_name = f"{output_folder}/{unique_suffix}_comfyui_output_sweep.log"

        self.logger = CustomLogger(self.log_file_name)
        self.requests = ComfyUIRequests(comfyui_url)

        # Log initialization
        self.logger.info("Initializing ComfyUISweep...")

    def _set_output_node(self, prompt: tuple[IComfyUIWorkflow, str]) -> None:
        """
        Set the output node in the JSON configuration.
        """
        prompt[0].set_output_filename(prompt[1].split("/")[-1])

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
            self.logger.info("First request saved to %s", output_file_path)

        if total_requests > 2:
            last_request = self.req_list[-1]

            output_file_path = (
                f"{self.log_file_name.split('.', maxsplit=1)[0]}_last.json"
            )
            with open(output_file_path, "w", encoding="utf-8") as file:
                json.dump(last_request[0].get_json(), file, indent=4)
            self.logger.info("Last request saved to %s", output_file_path)

        self.logger.info("--------------------------------------------------")

    def _log_explanation(self) -> None:
        """
        Log the explanation of the current configuration.
        """
        log_explanation0 = self.logger_explanation.split("/")[-1]
        log_explanation1 = self.logger_explanation.split("/")[:-1]
        self.logger.info("%s == %s", log_explanation0, log_explanation1)

        self.logger.info("--------------------------------------------------")

    def send_requests(self, delay_seconds: int = 0):
        """
        Send a request to ComfyUI with the current configuration.
        """
        i = 0  # Start with the first request
        total_requests = len(self.req_list)

        self._save_first_and_last_requests()
        self._log_explanation()

        while i < total_requests:
            req = self.req_list[i]
            self._set_output_node(req)

            try:
                print(f"Sending request {i + 1}/{total_requests}: {req[1]}")

                response = self.requests.comfyui_send_prompt(
                    json=req[0].get_json(), timeout=10
                )
                if not response.ok:
                    raise RuntimeError(f"Bad prompt: {response.status_code}")

                current_time = datetime.now()

                while True:
                    server_reply = self.requests.comfyui_get_queue()

                    if server_reply[1] == 0:
                        break

                    time.sleep(5)

                # Log success
                proccess_time_seconds = (datetime.now() - current_time).seconds
                print(
                    f"Request finished successfully after {proccess_time_seconds}s: {req[1]}"
                )

                output_name = f"{req[1].split('/')[-1]}_{str(i).zfill(5)}"

                history_status, history_entry = (
                    self.requests.comfyui_get_last_history_entry()
                )
                if history_status:
                    output_names = comfyui_get_history_output_name(history_entry)
                    if len(output_names) > 0:
                        output_name = output_names[-1]

                self.logger.info(
                    "%s == %s (%ds)",
                    output_name,
                    req[1].split("/")[:-1],
                    proccess_time_seconds
                )

                # Move to the next request
                i += 1
            except RuntimeError as e:
                raise e
            except RequestException as e:
                print(e)
                self.logger.error("Connection error: %s", e)

            time.sleep(delay_seconds)

    def add_animatediff_model_sweeper(self, model_name_list: list[str]) -> None:
        """
        Add the model sweeper to the JSON configuration.
        """
        local_req_list: list[tuple[IComfyUIWorkflow, str]] = []
        for model_name in model_name_list:
            for req in self.req_list:
                local_prompt = copy.deepcopy(req[0])

                local_prompt.set_animatediff_model(model_name)

                output_model_name = model_name.split(".")[0]
                output_file_name = f"{output_model_name}/{req[1]}"

                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = f"AnimateDiff_Model/{self.logger_explanation}"

    def add_stable_diffusion_model_sweeper(self, model_name_list: list[str]) -> None:
        """
        Add the model sweeper to the JSON configuration.
        """
        local_req_list: list[tuple[IComfyUIWorkflow, str]] = []
        for model_name in model_name_list:
            for req in self.req_list:
                local_prompt = copy.deepcopy(req[0])

                local_prompt.set_stable_diffusion_model(model_name)

                output_model_name = model_name.split(".")[0]
                output_file_name = f"{output_model_name}/{req[1]}"

                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = f"StableDiffusion_Model/{self.logger_explanation}"

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
            local_req_list: list[tuple[IComfyUIWorkflow, str]] = []
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
                    local_prompt = copy.deepcopy(req[0])

                    local_prompt.set_ksampler(
                        seed=seed,
                        steps=steps,
                        cfg=cfg,
                        sampler_name=sampler_name,
                        scheduler=scheduler,
                        denoise=denoise,
                    )

                    output_file_name = f"KSampler({seed}_{steps}_{cfg}_{sampler_name}_{scheduler}_{denoise})/{req[1]}"
                    local_req_list.append((local_prompt, output_file_name))

            self.req_list = local_req_list
            self.logger_explanation = f"KSampler(seed_steps_cfg_sampler_name_scheduler_denoise)/{self.logger_explanation}"
        except Exception as e:
            self.logger.error("Error in add_ksampler_sweeper: %s", e)
            raise

    def add_positive_prompt_sweeper(
        self,
        positive_prompt_list: list[str],
    ) -> None:
        """
        Add the positive prompt sweeper to the JSON configuration.
        """
        for i, pp in enumerate(positive_prompt_list):
            self.logger.info("Adding positive prompt %s: %s", i, pp)
            self.logger.info("--------------------------------------------------")

        local_req_list: list[tuple[IComfyUIWorkflow, str]] = []
        for req in self.req_list:
            for i, positive_prompt in enumerate(positive_prompt_list):
                local_prompt = copy.deepcopy(req[0])

                local_prompt.set_positive_prompt(positive_prompt)

                output_file_name = f"{req[1]}_pp{i}"
                local_req_list.append((local_prompt, output_file_name))

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
            self.logger.info("Adding negative prompt %s: %s", i, np)
            self.logger.info("--------------------------------------------------")

        local_req_list: list[tuple[IComfyUIWorkflow, str]] = []
        for req in self.req_list:
            for i, negative_prompt in enumerate(negative_prompt_list):
                local_prompt = copy.deepcopy(req[0])

                local_prompt.set_negative_prompt(negative_prompt)

                output_file_name = f"{req[1]}_np{i}"
                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = f"{self.logger_explanation}_NegativePrompt"

    def add_latent_image_sweeper(
        self,
        resolution_list: list[tuple[int, int]],
        batch_size_list: list[int],
    ) -> None:
        """
        Add the batch size sweeper to the JSON configuration.
        """
        for i, bs in enumerate(batch_size_list):
            self.logger.info("Adding batch size %s: %s", i, bs)
            self.logger.info("--------------------------------------------------")

        local_req_list: list[tuple[IComfyUIWorkflow, str]] = []
        for req in self.req_list:
            for i, (batch_size, resolution) in enumerate(
                product(batch_size_list, resolution_list)
            ):
                local_prompt = copy.deepcopy(req[0])

                local_prompt.set_latent_image(
                    batch_size=batch_size, resolution=resolution
                )

                output_file_name = f"Latent_Image({resolution[0]},{resolution[1]},{batch_size})/{req[1]}"
                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = (
            f"Latent_Image(width,height,batch_size)/{self.logger_explanation}"
        )
