"""
ComfyUI Automation Sweep Module
"""

import json

from .comfyui_requests import ComfyUIRequests
from .custom_logger import logger
from .comfyui_workflow import IComfyUIWorkflow


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
