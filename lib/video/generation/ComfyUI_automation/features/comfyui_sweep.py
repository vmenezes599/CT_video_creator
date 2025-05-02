"""
ComfyUI Automation Sweep Module
"""

import logging
import json
import copy
import time
from datetime import datetime
from itertools import product

import requests

from .comfyui_helpers import *


class ComfyUISweep:
    """
    Class to handle the sweep of parameters for ComfyUI.
    """

    def __init__(
        self,
        comfyui_url: str,
        output_node_index: int,
        workflow_json_path: str,
        output_folder: str = "output/",
        output_name: str = "output",
    ):
        with open(workflow_json_path, "r", encoding="utf-8") as file:
            self.base_json_config = json.load(file)

        self.comfyui_url = comfyui_url

        self.output_node_index = output_node_index
        self.logger_explanation = output_name

        self.req_list: list[tuple[dict, str]] = [
            (self.base_json_config.copy(), output_name)
        ]

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        unique_suffix = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")  # Timestamp
        log_file_name = f"{output_folder}/{unique_suffix}_comfyui_output_sweep.log"

        file_handler = logging.FileHandler(log_file_name)
        file_handler.setLevel(logging.INFO)

        # Create formatter and add it to the handler
        formatter = logging.Formatter(
            "%(message)s | %(asctime)s - %(levelname)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(file_handler)

        # Log initialization
        self.logger.info("Initializing ComfyUISweep...")

    def _set_output_node(self, prompt: tuple[dict, str]) -> None:
        """
        Set the output node in the JSON configuration.
        """
        index_str = f"{self.output_node_index}"
        prompt[0][index_str]["inputs"]["filename_prefix"] = prompt[1].split("/")[-1]

    def send_requests(self, delay_seconds: int = 0):
        """
        Send a request to ComfyUI with the current configuration.
        """
        i = 0  # Start with the first request
        total_requests = len(self.req_list)

        history_status, history = comfyui_get_history()
        if not history_status:
            print("Failed to fetch history. Exiting...")
            return

        history_previous_length = len(history)
        
        log_explanation0 = self.logger_explanation.split("/")[-1]
        log_explanation1 = self.logger_explanation.split("/")[:-1]
        self.logger.info("%s == %s",
                    log_explanation0,
                    log_explanation1)

        while i < total_requests:
            req = self.req_list[i]
            self._set_output_node(req)
            p = {"prompt": req[0]}

            try:
                # Simulate sending the request
                print(f"Sending request {i + 1}/{total_requests}: {req[1]}")

                # Uncomment this line to send the actual request
                response = requests.post(
                    f"{self.comfyui_url}/prompt", json=p, timeout=10
                )

                current_time = datetime.now()

                if not response.ok:
                    raise RuntimeError(f"Bad prompt: {response.status_code}")

                while True:
                    server_reply = comfyui_get_queue()

                    if not server_reply[0]:  # Server is down
                        raise ConnectionError("Server is down, retrying the request...")

                    if server_reply[1] == 0:
                        break

                    time.sleep(5)

                # Log success
                print(
                    f"Request finished successfully after {(datetime.now() - current_time).seconds}s: {req[1]}"
                )

                output_name = f"{req[1].split('/')[-1]}_{str(i).zfill(5)}"

                while True:
                    history_status, history = comfyui_get_history()

                    if (
                        not history_status
                        or len(history) == history_previous_length + i + 1
                    ):
                        break

                    time.sleep(5)

                history_status, history_entry = comfyui_get_last_history_entry()
                if history_status:
                    output_names = comfyui_get_history_output_name(history_entry)
                    if len(output_names) > 0:
                        output_name = output_names[-1]

                self.logger.info(
                    "%s == %s",
                    output_name,
                    req[1].split("/")[:-1],
                )

                # Move to the next request
                i += 1
                time.sleep(delay_seconds)

            except Exception as e:
                print(e)
                self.logger.error("Connection error: %s", e)
                server_reply = comfyui_get_queue()
                while not server_reply[0]:
                    time.sleep(5)  # Wait before retrying
                    server_reply = comfyui_get_queue()
                self.logger.info("Reconnected!")

    def add_animatediff_model_sweeper(
        self, animatediff_loader_node_index: int, model_name_list: list[str]
    ) -> None:
        """
        Add the model sweeper to the JSON configuration.
        """
        local_req_list: list[tuple[dict, str]] = []
        for model_name in model_name_list:
            for req in self.req_list:
                local_prompt = copy.deepcopy(req[0])

                index_str = f"{animatediff_loader_node_index}"

                local_prompt[index_str]["inputs"]["model_name"] = model_name

                output_model_name = model_name.split(".")[0]
                output_file_name = f"{output_model_name}/{req[1]}"

                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = f"AnimateDiff_Model/{self.logger_explanation}"

    def add_stable_diffusion_model_sweeper(
        self, stable_diffusion_loader_node_index: int, model_name_list: list[str]
    ) -> None:
        """
        Add the model sweeper to the JSON configuration.
        """
        local_req_list: list[tuple[dict, str]] = []
        for model_name in model_name_list:
            for req in self.req_list:
                local_prompt = copy.deepcopy(req[0])

                index_str = f"{stable_diffusion_loader_node_index}"

                local_prompt[index_str]["inputs"]["ckpt_name"] = model_name

                output_model_name = model_name.split(".")[0]
                output_file_name = f"{output_model_name}/{req[1]}"

                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = f"StableDiffusion_Model/{self.logger_explanation}"

    def add_ksampler_sweeper(
        self,
        ksampler_node_index: int,
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
        local_req_list: list[tuple[dict, str]] = []
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

                index_str = f"{ksampler_node_index}"

                local_prompt[index_str]["inputs"]["seed"] = seed
                local_prompt[index_str]["inputs"]["steps"] = steps
                local_prompt[index_str]["inputs"]["cfg"] = cfg
                local_prompt[index_str]["inputs"]["sampler_name"] = sampler_name
                local_prompt[index_str]["inputs"]["scheduler"] = scheduler
                local_prompt[index_str]["inputs"]["denoise"] = denoise

                output_file_name = f"KSampler({seed}_{steps}_{cfg}_{sampler_name}_{scheduler}_{denoise})/{req[1]}"
                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = f"KSampler(seed_steps_cfg_sampler_name_scheduler_denoise)/{self.logger_explanation}"

    def add_positive_prompt_sweeper(
        self,
        positive_prompt_node_index: int,
        positive_prompt_list: list[str],
    ) -> None:
        """
        Add the positive prompt sweeper to the JSON configuration.
        """
        for i, pp in enumerate(positive_prompt_list):
            self.logger.info("Adding positive prompt %s: %s", i, pp)
            self.logger.info("--------------------------------------------------")

        local_req_list: list[tuple[dict, str]] = []
        for req in self.req_list:
            for i, positive_prompt in enumerate(positive_prompt_list):
                local_prompt = copy.deepcopy(req[0])

                index_str = f"{positive_prompt_node_index}"

                local_prompt[index_str]["inputs"]["text"] = positive_prompt

                output_file_name = f"{req[1]}_pp{i}"
                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = f"{self.logger_explanation}_PositivePrompt"

    def add_negative_prompt_sweeper(
        self,
        negative_prompt_node_index: int,
        negative_prompt_list: list[str],
    ) -> None:
        """
        Add the negative prompt sweeper to the JSON configuration.
        """
        for i, np in enumerate(negative_prompt_list):
            self.logger.info("Adding negative prompt %s: %s", i, np)
            self.logger.info("--------------------------------------------------")

        local_req_list: list[tuple[dict, str]] = []
        for req in self.req_list:
            for i, negative_prompt in enumerate(negative_prompt_list):
                local_prompt = copy.deepcopy(req[0])

                index_str = f"{negative_prompt_node_index}"

                local_prompt[index_str]["inputs"]["text"] = negative_prompt

                output_file_name = f"{req[1]}_np{i}"
                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = f"{self.logger_explanation}_NegativePrompt"

    def add_latent_image_sweeper(
        self,
        latent_image_node_index: int,
        resolution_list: list[tuple[int, int]],
        batch_size_list: list[int],
    ) -> None:
        """
        Add the batch size sweeper to the JSON configuration.
        """
        for i, bs in enumerate(batch_size_list):
            self.logger.info("Adding batch size %s: %s", i, bs)
            self.logger.info("--------------------------------------------------")

        local_req_list: list[tuple[dict, str]] = []
        for req in self.req_list:
            for i, (batch_size, resolution) in enumerate(
                product(batch_size_list, resolution_list)
            ):
                local_prompt = copy.deepcopy(req[0])

                index_str = f"{latent_image_node_index}"

                local_prompt[index_str]["inputs"]["width"] = resolution[0]
                local_prompt[index_str]["inputs"]["height"] = resolution[1]
                local_prompt[index_str]["inputs"]["batch_size"] = batch_size

                output_file_name = f"Latent_Image({resolution[0]},{resolution[1]},{batch_size})/{req[1]}"
                local_req_list.append((local_prompt, output_file_name))

        self.req_list = local_req_list
        self.logger_explanation = (
            f"Latent_Image(width,height,batch_size)/{self.logger_explanation}"
        )
