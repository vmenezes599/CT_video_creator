"""
ComfyuiRequest is a class that handles HTTP requests to the ComfyUI API.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from ct_video_creator.environment_variables import COMFYUI_OUTPUT_FOLDER, COMFYUI_URL
from logging_utils import logger
from requests import Response, Session
from requests.exceptions import RequestException

from .comfyui_workflow import IComfyUIWorkflow


class ComfyUIRequests:
    """
    ComfyuiRequest is a class that handles HTTP requests to the ComfyUI API.
    """

    DEFAULT_CLEANUP_DELAY_SECONDS = 5

    def __init__(self, retries: int = 5, retry_delay: int = 1) -> None:
        """
        Initializes the ComfyuiRequest with a configurable retry mechanism.
        """
        self.retries = max(1, retries)
        self.retry_delay = max(0, retry_delay)
        self._delay_between_requests = self.retry_delay
        self._cleanup_delay_seconds = self.DEFAULT_CLEANUP_DELAY_SECONDS
        self.session: Session = requests.Session()

    def _send_get_request(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        stream: bool = False,
        timeout: float | tuple[float, float] = 10.0,
    ) -> Response:
        """
        Send a GET request using the configured session with simple retries.
        """
        last_exc: RequestException | None = None

        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.get(
                    url=url,
                    params=params,
                    stream=stream,
                    timeout=timeout,
                )
                response.raise_for_status()
                return response
            except RequestException as exc:
                last_exc = exc
                if attempt >= self.retries:
                    logger.error(
                        "GET %s failed after %s attempts. Last error: %s",
                        url,
                        self.retries,
                        exc,
                    )
                    raise

                logger.warning(
                    "GET %s failed on attempt %s/%s. Retrying in %s seconds. Error: %s",
                    url,
                    attempt,
                    self.retries,
                    self.retry_delay,
                    exc,
                )
                time.sleep(self.retry_delay)

        raise last_exc or RequestException("Unknown error during GET request.")

    def _send_post_request(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | tuple[float, float] = 10.0,
    ) -> Response:
        """
        Send a POST request using the configured session with retries.
        """
        last_exc: RequestException | None = None

        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.post(
                    url=url,
                    data=data,
                    json=json,
                    files=files,
                    params=params,
                    timeout=timeout,
                )
                response.raise_for_status()
                return response
            except RequestException as exc:
                last_exc = exc
                if attempt >= self.retries:
                    logger.error(
                        "POST %s failed after %s attempts. Last error: %s",
                        url,
                        self.retries,
                        exc,
                    )
                    raise

                logger.warning(
                    "POST %s failed on attempt %s/%s. Retrying in %s seconds. Error: %s",
                    url,
                    attempt,
                    self.retries,
                    self.retry_delay,
                    exc,
                )
                time.sleep(self.retry_delay)

        raise last_exc or RequestException("Unknown error during POST request.")

    def comfyui_get_heartbeat(self) -> bool:
        """
        Check if ComfyUI is running by sending a GET request to the heartbeat endpoint.
        """
        try:
            self._send_get_request(f"{COMFYUI_URL}/prompt", timeout=10)
            return True
        except RequestException:
            logger.error("Failed to fetch heartbeat from ComfyUI.")
            return False

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

    def _create_workflow_summary(self, workflow: IComfyUIWorkflow, max_length: int = 100) -> tuple[str, str]:
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

    def _wait_for_completion(self, prompt_id: str, check_interval: int = 1) -> int:
        """
        Wait for ComfyUI to complete processing the current request.

        :param prompt_id: The ID of the prompt to check
        :param check_interval: Seconds between queue checks
        :return: Processing time in seconds
        """
        start_time = datetime.now()

        while True:
            history = self.get_history()
            if prompt_id in history:
                break
            time.sleep(check_interval)

        return (datetime.now() - start_time).seconds

    def _send_clean_memory_request(self):
        """
        Send a request to clean memory in ComfyUI.
        """
        payload = {"unload_models": True, "free_memory": True}
        try:
            payload = {"unload_models": True, "free_memory": True}
            response = self._send_post_request(f"{COMFYUI_URL}/free", json=payload, timeout=10)
            if not response.ok:
                logger.error("Failed to clean memory in ComfyUI: {}", response.text)
            else:
                time.sleep(self._cleanup_delay_seconds)  # Give ComfyUI time to process the request
        except RequestException as e:
            logger.error("Error occurred while cleaning memory in ComfyUI: {}", e)

    def _comfyui_get_history_output_name(self, history_entry_dict: dict) -> list[str]:
        """
        Get the output names from a history entry dictionary.
        """

        result = []
        for _, output_types in history_entry_dict.get("outputs", {}).items():
            for _, value in output_types.items():
                for v in value:
                    if isinstance(v, dict) and "filename" in v:
                        result.append(v["filename"])
        return result

    def _get_output_paths(self, history_entry: dict) -> list[str]:
        """
        Get the output file paths for a completed workflow.

        :param history_entry: The history entry from ComfyUI
        :return: List of full paths to output files or empty list if not found
        """
        output_names = self._comfyui_get_history_output_name(history_entry)
        result = []
        if output_names:
            for name in output_names:
                result.append(os.path.join(COMFYUI_OUTPUT_FOLDER, name))
        return result

    def _check_for_output_success(self, response: dict):
        """
        Check if the response contains a successful output.

        :param response: The response dictionary from ComfyUI
        :return: True if output is successful, False otherwise
        """
        if response["status"]["status_str"] != "success":
            logger.error("ComfyUI request failed: {}", response["status"]["status_str"])
            raise RuntimeError(f"ComfyUI request failed: {response['status']['status_str']}")
        if response["status"]["completed"] is False:
            logger.error("ComfyUI request not completed successfully.")
            raise RuntimeError(f"ComfyUI request failed: {response['status']['status_str']}")

    def _process_single_workflow(self, workflow: IComfyUIWorkflow) -> list[str]:
        """
        Process a single workflow through the complete pipeline.

        :param workflow: The workflow to process
        :return: List of output file paths or empty list if processing failed
        """
        _, display_summary = self._create_workflow_summary(workflow)

        for attempt in range(1, self.retries + 1):
            try:
                response = self._submit_single_prompt(workflow)
                prompt_id = response.json()["prompt_id"]
                processing_time = self._wait_for_completion(prompt_id)

                logger.info(
                    "Request finished successfully after {}s: {}",
                    processing_time,
                    display_summary,
                )

                history_entry = self.get_last_history_entry()
                if history_entry:
                    self._check_for_output_success(history_entry)
                    return self._get_output_paths(history_entry)

                logger.error("No history entry found for request: {}", display_summary)

            except RuntimeError as err:
                logger.error(
                    "Failed to run workflow on attempt %s/%s for request %s: %s",
                    attempt,
                    self.retries,
                    display_summary,
                    err,
                )
            except RequestException as exc:
                logger.error(
                    "Connection error during request %s (attempt %s/%s): %s",
                    display_summary,
                    attempt,
                    self.retries,
                    exc,
                )
            finally:
                self._send_clean_memory_request()

        return []

    def upload_file(self, file_path: Path) -> Path:
        """
        Upload a file to ComfyUI.

        :param file_path: Path to the file to upload
        """
        try:
            url = f"{COMFYUI_URL}/upload/image"
            params = {"type": "input", "overwrite": "true"}

            with open(file_path, "rb") as file:
                files = {"image": file}
                self._send_post_request(url=url, params=params, files=files, timeout=30)

            logger.debug(f"File uploaded successfully: {file_path}")
        except (RequestException, OSError, IOError) as e:
            logger.error(f"Failed to upload file {file_path}: {e}")

        return Path(file_path.name)

    def download_all_files(self, files_to_download: list[Path], output_folder: Path) -> list[Path]:
        """
        Download all specified files from ComfyUI.

        :param files_to_download: List of file paths to download
        :param output_folder: Folder to save downloaded files
        :return: List of paths to downloaded files
        """
        output_paths: list[Path] = []
        for file_handler in files_to_download:
            params = {
                "filename": file_handler.name,
                "subfolder": "",
                "type": "output",
            }
            try:
                response = self._send_get_request(f"{COMFYUI_URL}/view", params=params, stream=True, timeout=120)
                response.raise_for_status()
                output_folder.mkdir(parents=True, exist_ok=True)
                out_path = output_folder / file_handler.name
                with open(out_path, "wb") as file_handler:
                    for chunk in response.iter_content(2 * 1024 * 1024):
                        if chunk:
                            file_handler.write(chunk)
                output_paths.append(out_path)
            except RequestException as e:
                logger.warning(f"Failed to download file {file_handler.name}: {e}")

        return output_paths

    def ensure_send_all_prompts(self, req_list: list[IComfyUIWorkflow], output_dir: Path) -> list[Path]:
        """
        Send all prompts in the list to ComfyUI and wait for them to finish.

        :param req_list: List of workflows to process
        :return: List of output file paths for successful requests
        """
        logger.info(f"Sending {len(req_list)} requests to ComfyUI...")

        output_image_paths: list[str] = []

        for index, workflow in enumerate(req_list, 1):
            logger.info(f"Processing request {index}/{len(req_list)}")
            output_paths = self._process_single_workflow(workflow)
            output_image_paths.extend(output_paths)
            if self._delay_between_requests > 0:
                time.sleep(self._delay_between_requests)

        logger.info("Finished processing all ComfyUI requests.")

        downloaded_files = self.download_all_files([Path(p) for p in output_image_paths], output_folder=output_dir)

        if len(downloaded_files) < len(req_list):
            logger.error("No files were downloaded from ComfyUI.")
            raise RequestException("Failed to generate assets from workflows.")

        return downloaded_files

    def get_processing_queue(self) -> int:
        """
        Get the queue information from ComfyUI.
        """
        try:
            response = self._send_get_request(f"{COMFYUI_URL}/prompt", timeout=10)
            queue_data = response.json()
            return queue_data["exec_info"]["queue_remaining"]
        except RequestException as exc:
            logger.error(f"Failed to fetch queue: {exc}")
            return -1

    def get_history(self) -> dict:
        """
        Get the history information from ComfyUI.
        """
        try:
            response = self._send_get_request(f"{COMFYUI_URL}/history", timeout=10)
            return response.json()
        except RequestException as exc:
            logger.error(f"Failed to fetch history: {exc}")
            return {}

    def get_last_history_entry(self) -> dict:
        """
        Get the last history entry from ComfyUI.
        """
        history = self.get_history()

        if history:
            # Get the last key from the dictionary
            last_key = list(history.keys())[-1]
            return history[last_key]

        logger.error("Failed to fetch last history entry.")
        return {}

    def get_available_loras(self) -> list[str]:
        """
        Get the list of available LORA models from ComfyUI.
        """
        try:
            response = self._send_get_request(f"{COMFYUI_URL}/models/loras", timeout=10)
            return response.json()
        except RequestException as exc:
            logger.error(f"Failed to fetch available LORA models: {exc}")
            return []
