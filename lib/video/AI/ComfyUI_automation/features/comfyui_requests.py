"""
ComfyuiRequest is a class that handles HTTP requests to the ComfyUI API.
"""

from datetime import datetime
import time

import requests
from requests.exceptions import RequestException

from .comfyui_helpers import comfyui_get_history_output_name
from .custom_logger import logger


class ComfyUIRequests:
    """
    ComfyuiRequest is a class that handles HTTP requests to the ComfyUI API.
    """

    def __init__(self, comfyui_url: str, delay_seconds: int = 10) -> None:
        """
        Initializes the ComfyuiRequest with a configurable retry mechanism.
        """
        self.comfyui_url = comfyui_url
        self.delay_seconds = delay_seconds

    def _send_get_request(self, url: str, timeout: int = 10):
        """
        Sends a GET request using the configured session.
        """
        return requests.get(url=url, timeout=timeout)

    def _send_post_request(
        self, url: str, data: dict = None, json: dict = None, timeout: int = 10
    ):
        """
        Sends a POST request using the configured session.
        """
        return requests.post(url=url, data=data, json=json, timeout=timeout)

    def comfyui_get_heartbeat(self) -> bool:
        """
        Check if ComfyUI is running by sending a GET request to the heartbeat endpoint.
        """
        response = self._send_get_request(f"{self.comfyui_url}/prompt", timeout=10)
        return response.ok

    def comfyui_send_prompt(self, json: dict, timeout: int = 10) -> tuple[bool, dict]:
        """
        Send a prompt to the ComfyUI API.

        :param prompt: The prompt data to send as a dictionary.
        :param timeout: The timeout for the request in seconds.
        :return: A tuple containing a success flag (True/False) and the response data or an error message.
        """
        if not isinstance(json, dict):
            raise ValueError("The prompt must be a dictionary.")

        url = f"{self.comfyui_url}/prompt"
        prompt = {"prompt": json}

        return self._send_post_request(url=url, json=prompt, timeout=timeout)

    def comfyui_ensure_send_all_prompts(self, req_list: list[dict]) -> bool:
        """
        Send all prompts in the list to ComfyUI and wait for them to finish.
        """

        output_image_paths: list[str] = []
        total_requests = len(req_list)
        i = 0
        while i < total_requests:
            req = req_list[i]

            try:
                print(f"Sending request {i + 1}/{total_requests}: {req[1]}")

                response = self.comfyui_send_prompt(json=req[0].get_json(), timeout=10)
                if not response.ok:
                    raise RuntimeError(f"Bad prompt: {response.status_code}")

                current_time = datetime.now()

                while True:
                    server_reply = self.comfyui_get_queue()

                    if server_reply[1] == 0:
                        break

                    time.sleep(5)

                # Log success
                proccess_time_seconds = (datetime.now() - current_time).seconds
                print(
                    f"Request finished successfully after {proccess_time_seconds}s: {req[1]}"
                )

                output_name = f"{req[1].split('/')[-1]}_{str(i).zfill(5)}"

                history_status, history_entry = self.comfyui_get_last_history_entry()
                if history_status:
                    output_names = comfyui_get_history_output_name(history_entry)
                    if len(output_names) > 0:
                        output_name = output_names[-1]

                    full_path_name = comfyui_get_history_output_name(
                        history_entry_dict=history_entry, use_full_path=True
                    )
                    output_image_paths.append(full_path_name[-1])

                logger.info(
                    "%s == %s (%ds)",
                    output_name,
                    req[1].split("/")[:-1],
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

    def comfyui_get_queue(self) -> tuple[bool, int]:
        """
        Get the queue information from ComfyUI.
        """
        response = self._send_get_request(f"{self.comfyui_url}/prompt", timeout=10)

        if response.ok:
            queue_data = response.json()
            return (True, queue_data["exec_info"]["queue_remaining"])

        print(f"Failed to fetch queue. Status code: {response.status_code}")
        return (False, -1)

    def comfyui_get_history(self) -> tuple[bool, list]:
        """
        Get the history information from ComfyUI.
        """
        response = self._send_get_request(f"{self.comfyui_url}/history", timeout=10)

        if response.ok:
            history_data = response.json()
            return (True, history_data)

        print(f"Failed to fetch history. Status code: {response.status_code}")

    def comfyui_get_last_history_entry(self) -> tuple[bool, list]:
        """
        Get the history information from ComfyUI.
        """
        response = self._send_get_request(f"{self.comfyui_url}/history", timeout=10)

        if response.ok:
            history_data = response.json()
            last_key = list(history_data.keys())[-1]
            return (True, history_data[last_key])

        print(f"Failed to fetch history. Status code: {response.status_code}")
        return (False, [])
