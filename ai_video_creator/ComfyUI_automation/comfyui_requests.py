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

    def __init__(
        self, max_retries_per_request: int = 5, delay_seconds: int = 10
    ) -> None:
        """
        Initializes the ComfyuiRequest with a configurable retry mechanism.
        """
        self.max_retries_per_request = max_retries_per_request
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
        response = requests.post(url=url, data=data, json=json, timeout=timeout)
        response.raise_for_status()
        return response

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

    def _create_progress_summary(
        self, workflow: IComfyUIWorkflow, max_length: int = 100
    ) -> tuple[str, str]:
        """
        Create a progress summary for displaying workflow information.

        :param workflow: The workflow to summarize
        :param max_length: Maximum length for display summary
        :return: Tuple of (full_summary, display_summary)
        """
        full_summary = workflow.get_workflow_summary()
        if len(full_summary) > max_length:
            display_summary = full_summary[:max_length] + "..."
        else:
            display_summary = full_summary
        return full_summary, display_summary

    def _submit_single_prompt(self, workflow: IComfyUIWorkflow) -> requests.Response:
        """
        Submit a single prompt to ComfyUI.

        :param workflow: The workflow to submit
        :return: Response from ComfyUI
        :raises RuntimeError: If the prompt submission fails
        """
        json_req = workflow.get_json()
        response = self.comfyui_send_prompt(json=json_req, timeout=10)
        return response

    def _wait_for_completion(self, prompt_id: str, check_interval: int = 5) -> int:
        """
        Wait for ComfyUI to complete processing the current request.

        :param prompt_id: The ID of the prompt to check
        :param check_interval: Seconds between queue checks
        :return: Processing time in seconds
        """
        start_time = datetime.now()

        while True:
            history = self.comfyui_get_history()
            if prompt_id in history:
                break
            time.sleep(check_interval)

        return (datetime.now() - start_time).seconds

    def _get_output_path(self, history_entry: dict) -> str | None:
        """
        Get the output file path for a completed workflow.

        :param workflow: The workflow that was processed
        :param index: Index of the workflow in the batch
        :return: Full path to output file or None if not found
        """
        output_names = comfyui_get_history_output_name(history_entry)
        if output_names:
            actual_output_name = output_names[0]
            return os.path.join(COMFYUI_OUTPUT_FOLDER, actual_output_name)

        return None

    def _check_for_output_success(self, response: dict):
        """
        Check if the response contains a successful output.

        :param response: The response dictionary from ComfyUI
        :return: True if output is successful, False otherwise
        """
        if response["status"]["status_str"] != "success":
            logger.error("ComfyUI request failed: %s", response["status"]["status_str"])
            raise RuntimeError(
                f"ComfyUI request failed: {response['status']['status_str']}"
            )
        if response["status"]["completed"] is False:
            logger.error("ComfyUI request not completed successfully.")
            raise RuntimeError(
                f"ComfyUI request failed: {response['status']['status_str']}"
            )

    def _process_single_workflow(self, workflow: IComfyUIWorkflow) -> str | None:
        """
        Process a single workflow through the complete pipeline.

        :param workflow: The workflow to process
        :param index: Current workflow index (0-based)
        :param total: Total number of workflows
        :return: Output file path or None if processing failed
        """
        _, display_summary = self._create_progress_summary(workflow)

        tries = 0
        while tries < self.max_retries_per_request:
            try:
                # Submit the prompt
                response = self._submit_single_prompt(workflow)
                response_data = response.json()

                prompt_id = response_data["prompt_id"]

                # Wait for completion and track timing
                processing_time = self._wait_for_completion(prompt_id)

                logger.info(
                    "Request finished successfully after %ds: %s",
                    processing_time,
                    display_summary,
                )

                # Get output path
                history_entry = self.comfyui_get_last_history_entry()

                if history_entry:
                    self._check_for_output_success(history_entry)
                    output_path = self._get_output_path(history_entry)

                    return output_path
                tries += 1

            except RuntimeError:
                tries += 1
                logger.error(
                    "Failed to run workflow on attempt %d/%d for request: %s",
                    tries,
                    self.max_retries_per_request,
                    display_summary,
                )
                if tries < self.max_retries_per_request:
                    time.sleep(self.delay_seconds)
            except RequestException as e:
                logger.error(
                    "Connection error during request %s: %s", display_summary, e
                )
                time.sleep(self.delay_seconds)

        # If all retries exhausted
        logger.error(
            "Failed to process workflow after %d attempts: %s",
            self.max_retries_per_request,
            display_summary,
        )
        return None

    def comfyui_ensure_send_all_prompts(
        self, req_list: list[IComfyUIWorkflow]
    ) -> list[str]:
        """
        Send all prompts in the list to ComfyUI and wait for them to finish.

        :param req_list: List of workflows to process
        :return: List of output file paths for successful requests
        """
        output_image_paths: list[str] = []

        for workflow in req_list:
            output_path = self._process_single_workflow(workflow)
            if output_path:
                output_image_paths.append(output_path)

            # Add delay between requests
            time.sleep(self.delay_seconds)

        return output_image_paths

    def comfyui_get_processing_queue(self) -> int:
        """
        Get the queue information from ComfyUI.
        """
        response = self._send_get_request(f"{COMFYUI_URL}/prompt", timeout=10)

        if response.ok:
            queue_data = response.json()
            return queue_data["exec_info"]["queue_remaining"]

        logger.error("Failed to fetch queue.")
        return -1

    def comfyui_get_history(self) -> dict:
        """
        Get the history information from ComfyUI.
        """
        response = self._send_get_request(f"{COMFYUI_URL}/history", timeout=10)

        if response.ok:
            history_data = response.json()
            return history_data

        logger.error("Failed to fetch history.")
        return {}

    def comfyui_get_last_history_entry(self) -> dict:
        """
        Get the last history entry from ComfyUI.
        """
        history = self.comfyui_get_history()

        if history:
            # Get the last key from the dictionary
            last_key = list(history.keys())[-1]
            return history[last_key]

        logger.error("Failed to fetch last history entry.")
        return {}
