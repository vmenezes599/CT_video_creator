"""
ComfyuiRequest is a class that handles HTTP requests to the ComfyUI API.
"""

import os
import time
from datetime import datetime

import requests
from logging_utils import logger
from requests.exceptions import RequestException

from ai_video_creator.environment_variables import COMFYUI_OUTPUT_FOLDER, COMFYUI_URL

from .comfyui_helpers import comfyui_get_history_output_name
from .comfyui_workflow import IComfyUIWorkflow


class ComfyUIRequests:
    """
    ComfyuiRequest is a class that handles HTTP requests to the ComfyUI API.
    """

    def __init__(self, delay_seconds: int = 10) -> None:
        """
        Initializes the ComfyuiRequest with a configurable retry mechanism.
        """
        self.delay_seconds = delay_seconds

    def _send_get_request(self, url: str, timeout: int = 10):
        """
        Sends a GET request using the configured session.
        """
        return requests.get(url=url, timeout=timeout)

    def _send_post_request(
        self, url: str, data: dict = None, json: dict = None, timeout: int = 10
    ) -> requests.Response:
        """
        Sends a POST request using the configured session.
        """
        return requests.post(url=url, data=data, json=json, timeout=timeout)

    def comfyui_get_heartbeat(self) -> bool:
        """
        Check if ComfyUI is running by sending a GET request to the heartbeat endpoint.
        """
        response = self._send_get_request(f"{COMFYUI_URL}/prompt", timeout=10)
        return response.ok

    def comfyui_send_prompt(self, json: dict, timeout: int = 10) -> requests.Response:
        """
        Send a prompt to the ComfyUI API.

        :param json: The prompt data to send as a dictionary.
        :param timeout: The timeout for the request in seconds.
        :return: A tuple containing a success flag (True/False) and the response data or an error message.
        """
        if not isinstance(json, dict):
            raise ValueError("The prompt must be a dictionary.")

        url = f"{COMFYUI_URL}/prompt"
        prompt = {"prompt": json}

        return self._send_post_request(url=url, json=prompt, timeout=timeout)

    def comfyui_ensure_send_all_prompts(
        self, req_list: list[IComfyUIWorkflow]
    ) -> list[str]:  # 28
        """
        Send all prompts in the list to ComfyUI and wait for them to finish.
        """

        output_image_paths: list[str] = []
        total_requests = len(req_list)
        i = 0
        while i < total_requests:
            req = req_list[i]

            try:
                print_summary_max_length = 100
                full_summary = req.get_workflow_summary()
                smaller_workflow_summary = full_summary[
                    : min(print_summary_max_length, len(full_summary))
                ]
                if len(full_summary) > print_summary_max_length:
                    smaller_workflow_summary += "..."

                print(
                    f"Sending request {i + 1}/{total_requests}: {smaller_workflow_summary}"
                )

                json_req = req.get_json()
                response = self.comfyui_send_prompt(json=json_req, timeout=10)
                if not response.ok:
                    raise RuntimeError(f"Bad prompt: {response.status_code}")

                current_time = datetime.now()

                # Wait for the request to finish
                while True:
                    server_reply = self.comfyui_get_queue()

                    if server_reply[1] == 0:
                        break

                    time.sleep(5)

                # Log success
                proccess_time_seconds = (datetime.now() - current_time).seconds
                print(
                    f"Request finished successfully after {proccess_time_seconds}s: {smaller_workflow_summary}"
                )

                output_name = f"{full_summary.split('/')[-1]}_{str(i).zfill(5)}"

                history_status, history_entry = self.comfyui_get_last_history_entry()
                if history_status:
                    output_names = comfyui_get_history_output_name(history_entry)

                    if len(output_names) > 0:
                        output_name = output_names[0]

                        full_path_name = os.path.join(
                            COMFYUI_OUTPUT_FOLDER, output_name
                        )
                        output_image_paths.append(full_path_name)

                logger.info(
                    "%s == %s (%ds)",
                    output_name,
                    full_summary.split("/")[:-1],
                    proccess_time_seconds,
                )

                # Move to the next request
                i += 1
            except RuntimeError as e:
                raise e
            except RequestException as e:
                print(e)
                logger.error("Connection error: %s", e)

            time.sleep(self.delay_seconds)

        return output_image_paths

    def comfyui_get_queue(self) -> tuple[bool, int]:
        """
        Get the queue information from ComfyUI.
        """
        response = self._send_get_request(f"{COMFYUI_URL}/prompt", timeout=10)

        if response.ok:
            queue_data = response.json()
            return (True, queue_data["exec_info"]["queue_remaining"])

        print(f"Failed to fetch queue. Status code: {response.status_code}")
        return (False, -1)

    def comfyui_get_history(self) -> tuple[bool, list]:
        """
        Get the history information from ComfyUI.
        """
        response = self._send_get_request(f"{COMFYUI_URL}/history", timeout=10)

        if response.ok:
            history_data = response.json()
            return (True, history_data)

        print(f"Failed to fetch history. Status code: {response.status_code}")

    def comfyui_get_last_history_entry(self) -> tuple[bool, list]:
        """
        Get the history information from ComfyUI.
        """
        response = self._send_get_request(f"{COMFYUI_URL}/history", timeout=10)

        if response.ok:
            history_data = response.json()
            last_key = list(history_data.keys())[-1]
            return (True, history_data[last_key])

        print(f"Failed to fetch history. Status code: {response.status_code}")
        return (False, [])
