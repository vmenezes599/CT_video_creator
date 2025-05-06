"""
ComfyuiRequest is a class that handles HTTP requests to the ComfyUI API.
"""

import requests


class ComfyUIRequests:
    """
    ComfyuiRequest is a class that handles HTTP requests to the ComfyUI API.
    """

    def __init__(self, comfyui_url: str):
        """
        Initializes the ComfyuiRequest with a configurable retry mechanism.
        """
        self.comfyui_url = comfyui_url

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
